import datetime
from webob import Response
from plumber import plumber
from zope.component import queryUtility
from pyramid.interfaces import IResponseFactory
from pyramid.view import view_config
from yafowil.base import (
    factory,
    UNSET,
)
from cone.tile import (
    tile,
    registerTile,
    Tile,
)
from cone.app.browser.utils import make_url
from cone.app.browser.layout import ProtectedContentTile
from cone.app.browser.form import Form
from cone.app.browser.authoring import (
    AddPart,
    EditPart,
)
from cone.mdb.model import (
    RevisionAdapter,
    add_revision,
    update_revision,
    solr_config,
)
from cone.mdb.solr import (
    Term,
    SOLR_FIELDS,
    Metadata as SolrMetadata,
)


@tile('revisiondetails', 'templates/revisiondetails.pt',
      interface=RevisionAdapter, permission='view')
class RevisionDetails(Tile):
    
    def format_date(self, val):
        if not val:
            return u''
        if isinstance(val, datetime.datetime):
            return val.strftime('%d.%m.%Y - %H:%M')
        return val
    
    @property
    def relations(self):
        """XXX: move relations lookup
        """
        relations = self.model.metadata.relations
        ret = list()
        if not relations:
            return ret
        query = Term('uid', relations[0])
        for rel in relations[1:]:
            query = query | Term('uid', rel)
        md = SolrMetadata(solr_config(self.model), SOLR_FIELDS)
        for relmd in md.query(q=query, fl='title,path'):
            ret.append({
                'target': '%s/%s' % (self.request.application_url, relmd.path),
                'title': relmd.title,
            })
        return ret


@view_config('download', for_=RevisionAdapter, permission='view')
def download(model, request):
    response_factory = queryUtility(IResponseFactory, default=Response)
    response = response_factory(model.model['binary'].payload)
    response.content_type = model.metadata.mimetype
    response.content_disposition = 'attachment'
    return response


class RevisionForm(object):
    
    form_name = 'revisionform'
    
    def prepare(self):
        metadata = self.model.metadata
        resource = self.action_resource
        action = make_url(self.request, node=self.model, resource=resource)
        form = factory(
            u'form',
            name = self.form_name,
            props = {
                'action': action,
            })
        form['visibility'] = factory(
            'field:label:error:select',
            value = metadata.visibility,
            props = {
                'label': 'Visibility',
                'vocabulary': self.visibility_vocab,
            })
        form['title'] = factory(
            'field:label:error:text',
            value = metadata.title,
            props = {
                'required': 'No revision title given',
                'label': 'Revision title',
            })
        form['author'] = factory(
            'field:label:text',
            value = metadata.author,
            props = {
                'label': 'Document author',
            })
        form['description'] = factory(
            'field:label:error:textarea',
            value = metadata.description,
            props = {
                'label': 'Revision description',
                'rows': 5,
            })
        form['keywords'] = factory(
            'field:label:*keywords:textarea',
            value = self.keywords_value,
            props = {
                'label': 'Keywords',
                'rows': 5,
            },
            custom = {
                'keywords': ([self.keywords_extractor], [], [], []),
            })
        relations_target = make_url(
            self.request, node=self.model.root['repositories'])
        form['relations'] = factory(
            'field:label:*relations:reference',
            value = self.relations_value,
            props = {
                'label': 'Relations',
                'multivalued': True,
                'target': relations_target,
                'vocabulary': self.relations_vocab,
            },
            custom = {
                'relations': ([self.relations_extractor], [], [], []),
            })
        form['effective'] = factory(
            'field:label:error:datetime',
            value = metadata.effective,
            props = {
                'label': 'Effective date',
                'datepicker': True,
                'time': True,
                'locale': 'de',
            })
        form['expires'] = factory(
            'field:label:error:datetime',
            value = metadata.expires,
            props = {
                'label': 'Expiration date',
                'datepicker': True,
                'time': True,
                'locale': 'de',
            })
        form['alttag'] = factory(
            'field:label:text',
            value = metadata.alttag,
            props = {
                'label': 'Alt Tag for publishing',
            })
        # XXX: rename to file somewhen
        form['data'] = factory(
            'field:label:error:file',
            value = self.data_value,
            props = {
                'label': 'Data',
                'required': 'No file uploaded',
            })
        form['save'] = factory(
            'submit',
            props = {
                'action': 'save',
                'expression': True,
                'handler': self.save,
                'next': self.next,
                'label': 'Save',
            })
        form['cancel'] = factory(
            'submit',
            props = {
                'action': 'cancel',
                'expression': True,
                'handler': None,
                'next': self.next,
                'label': 'Cancel',
                'skip': True,
            })
        self.form = form
    
    @property
    def visibility_vocab(self):
        if self.model.state == u'active':
            return [('anonymous', 'Anonymous')]
        return [
            ('hidden', 'Hidden'),
            ('anonymous', 'Anonymous'),
        ]
    
    @property
    def relations_vocab(self):
        """XXX: move relations lookup
        """
        vocab = list()
        relations = self.model.metadata.relations
        if not relations:
            return vocab
        md = SolrMetadata(solr_config(self.model), SOLR_FIELDS)
        for relation in relations:
            rel = md.query(q='uid:%s' % relation, fl='title')
            if rel and rel[0].get('title'):
                title = rel[0].title
            else:
                # happens if relation is not found in solr
                title = relation
            vocab.append((relation, title))
        return vocab
    
    @property
    def relations_value(self):
        relations = self.relations_vocab
        return [rel[0] for rel in relations]
    
    @property
    def keywords_value(self):
        keywords = self.model.metadata.keywords
        if not keywords:
            keywords = list()
        return u'\n'.join(keywords)
    
    @property
    def data_value(self):
        payload = None
        if self.model.__name__ is not None:
            payload = self.model.model['binary'].payload
        return payload
    
    def keywords_extractor(self, widget, data):
        if data.extracted is UNSET:
            return []
        keywords = data.extracted.split('\n')
        return [kw.strip('\r') for kw in keywords if kw]
    
    def relations_extractor(self, widget, data):
        relations = data.extracted
        if relations is UNSET:
            relations = list()
        if isinstance(relations, basestring):
            relations = [relations]
        return [rel for rel in relations if rel]
    
    def _field_id(self, s):
        return u'%s.%s' % (self.form_name, s)
    
    def _fetch(self, data, name):
        return data.fetch(self._field_id(name)).extracted

    def revision_data(self, data):
        f = self._fetch
        data = {
            'title': f(data, u'title'),
            'author': f(data, u'author'),
            'description': f(data, u'description'),
            'keywords': f(data, u'keywords'),
            'relations': f(data, u'relations'),
            'effective': f(data, u'effective'),
            'expires': f(data, u'expires'),
            'alttag': f(data, u'alttag'),
            'data': f(data, u'data'),
            'visibility': f(data, u'visibility'),
        }
        return data


registerTile('content',
             'templates/revision.pt',
             interface=RevisionAdapter,
             class_=ProtectedContentTile,
             permission='login',
             strict=False)


@tile('addform', interface=RevisionAdapter, permission="add")
class RevisionAddForm(RevisionForm, Form):
    __metaclass__ = plumber
    __plumbing__ = AddPart
    
    def save(self, widget, data):
        revision = add_revision(
            self.request,
            self.model.__parent__,
            self.revision_data(data))
        self.model.__name__ = revision.__name__
        

@tile('editform', interface=RevisionAdapter, permission="edit")
class RevisionEditForm(RevisionForm, Form):
    __metaclass__ = plumber
    __plumbing__ = EditPart
    
    def save(self, widget, data):
        update_revision(self.request,
                        self.model,
                        self.revision_data(data))