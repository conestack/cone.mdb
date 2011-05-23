import os
import datetime
from webob import Response
from plumber import plumber
from zope.component import queryUtility
from pyramid.interfaces import IResponseFactory
from pyramid.view import view_config
from yafowil.base import UNSET
from cone.tile import (
    tile,
    registerTile,
    Tile,
)
from cone.app.browser.utils import make_url
from cone.app.browser.layout import ProtectedContentTile
from cone.app.browser.form import (
    Form,
    YAMLForm,
)
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
    __metaclass__ = plumber
    __plumbing__ = YAMLForm
    
    form_template_path = os.path.join(os.path.dirname(__file__),
                                      'forms/revision.yaml')
    
    def visibility_vocab(self):
        if self.model.state == u'active':
            return [('anonymous', 'Anonymous')]
        return [
            ('hidden', 'Hidden'),
            ('anonymous', 'Anonymous'),
        ]
    
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
    
    def relations_value(self, widget, data):
        relations = self.relations_vocab()
        return [rel[0] for rel in relations]
    
    def relations_target(self):
        return make_url(self.request, node=self.model.root['repositories'])
    
    def keywords_value(self, widget, data):
        keywords = self.model.metadata.keywords
        if not keywords:
            keywords = list()
        return u'\n'.join(keywords)
    
    def data_value(self, widget, data):
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
        return u'revisionform.%s' % s
    
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