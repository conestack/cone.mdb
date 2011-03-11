import uuid
import datetime
from webob import Response
from zope.component import queryUtility
from pyramid.interfaces import IResponseFactory
from pyramid.view import bfg_view
from yafowil.base import (
    factory,
    ExtractionError,
)
from cone.tile import (
    tile,
    render_tile,
    registerTile,
    Tile,
)
from pyramid.security import authenticated_userid
from cone.app.browser.utils import (
    make_url,
    nodepath,
    format_date,
)
from cone.app.browser.layout import ProtectedContentTile
from cone.app.browser.form import (
    AddForm,
    EditForm,
)
from node.ext.mdb import (
    Revision,
    Metadata,
    Binary,
)
from cone.mdb.model.revision import RevisionAdapter
from cone.mdb.browser.utils import (
    timestamp,
    solr_config,
)
from cone.mdb.solr import Metadata as SolrMetadata


@tile('revisiondetails', 'templates/revisiondetails.pt',
      interface=RevisionAdapter, permission='view')
class RevisionDetails(Tile):
    
    @property
    def relations(self):
        relations = self.model.metadata.relations
        ret = list()
        if not relations:
            return ret
        query = ''
        for rel in relations:
            query = '%suid:%s OR ' % (query, rel)
        query = query.strip(' OR ')
        md = SolrMetadata(solr_config(self.model))
        for relmd in md.query(q=query):
            ret.append({
                'target': '%s/%s' % (self.request.application_url, relmd.path),
                'title': relmd.title,
            })
        return ret


@bfg_view(name='download', for_=RevisionAdapter, permission='view')
def download(model, request):
    response_factory = queryUtility(IResponseFactory, default=Response)
    response = response_factory(model.model['binary'].payload)
    response.content_type = model.metadata.metatype
    response.content_disposition = 'attachment'
    return response


class RevisionForm(object):
    
    @property
    def prepare(self):
        metadata = self.model.metadata
        resource = self.adding and 'add' or 'edit'
        action = make_url(self.request, node=self.model, resource=resource)
        form = factory(u'form',
                       name='revisionform',
                       props={'action': action})
        form['visibility'] = factory(
            'field:label:error:select',
            value = metadata.visibility,
            props = {
                'label': 'Visibility',
                'vocabulary': self.visibility_vocab,
            })
        form['flag'] = factory(
            'field:label:error:select',
            value = metadata.flag,
            props = {
                'label': 'Flag',
                'vocabulary': self.flag_vocab,
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
            'field:label:textarea',
            value = self.keywords,
            props = {
                'label': 'Keywords',
                'rows': 5,
            })
        relations = self.relations
        form['relations'] = factory(
            'field:label:reference',
            value = [rel[0] for rel in relations],
            props = {
                'label': 'Relations',
                'multivalued': True,
                'vocabulary': relations,
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
        payload = None
        if self.model.__name__ is not None:
            payload = self.model.model['binary'].payload
        form['data'] = factory(
            'field:label:error:file',
            value = payload,
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
    def adding(self):
        return self.model.__name__ is None
    
    @property
    def visibility_vocab(self):
        if self.adding or self.model.metadata.flag == 'draft':
            return [('hidden', 'hidden')]
        return [
            ('hidden', 'Hidden'),
            ('anonymous', 'Anonymous'),
        ]
        
    @property
    def flag_vocab(self):
        if self.adding:
            return [('draft', 'Draft')]
        if self.model.metadata.flag == 'draft':
            return [
                ('draft', 'Draft'),
                ('active', 'Active'),
            ]
        if self.model.metadata.flag == 'active':
            return [
                ('active', 'Active'),
            ]
        if self.model.metadata.flag == 'frozen':
            return [('frozen', 'Frozen')]
    
    @property
    def keywords(self):
        keywords = self.model.metadata.keywords
        if not keywords:
            keywords = list()
        return u'\n'.join(keywords)
    
    @property
    def relations(self):
        vocab = list()
        relations = self.model.metadata.relations
        if not relations:
            return vocab
        md = SolrMetadata(solr_config(self.model))
        for relation in relations:
            rel = md.query(q='uid:%s' % relation)
            if rel and rel[0].get('title'):
                title = rel[0].title
            else:
                title = relation
            vocab.append((relation, title))
        return vocab

    def set_metadata_from_form(self, metadata, data):
        def id(s):
            return 'revisionform.%s' % s
        metadata.title = data.fetch(id('title')).extracted
        metadata.author = data.fetch(id('author')).extracted
        metadata.description = data.fetch(id('description')).extracted
        keywords = data.fetch(id('keywords')).extracted.split('\n')
        keywords = [kw.strip('\r') for kw in keywords if kw]
        metadata.keywords = keywords
        relations = data.fetch(id('relations')).extracted
        if not relations:
            relations = list()
        if isinstance(relations, basestring):
            relations = [relations]
        metadata.relations = relations
        metadata.effective = data.fetch(id('effective')).extracted
        metadata.expires = data.fetch(id('expires')).extracted
        metadata.alttag = data.fetch(id('alttag')).extracted
        body = ' '.join([
            metadata.title,
            metadata.description, 
            metadata.author,
            metadata.alttag,
            data.fetch(id('keywords')).extracted,
            ])
        metadata.body = body
    
    def index_metadata_in_solr(self, model):
        try:
            metadata = model.metadata
            path = '/'.join(nodepath(model))
            kw = {
                'uid': metadata.uid,
                'author': metadata.author,
                'revision': model.__name__,
                'metatype': metadata.metatype,
                'creator': metadata.creator,
                'keywords': metadata.keywords,
                'url': '', # XXX
                'relations': metadata.relations,
                'title': metadata.title,
                'description': metadata.description,
                'alttag': metadata.alttag,
                'body': metadata.body,
                'flag': metadata.flag,
                'visibility': metadata.visibility,
                'path': path,
                'filename': metadata.filename,
            }
            self.solr_date(metadata.created, kw, 'created')
            self.solr_date(metadata.effective, kw, 'effective')
            self.solr_date(metadata.expires, kw, 'expires')
            self.solr_date(metadata.modified, kw, 'modified')
            md = SolrMetadata(solr_config(model), **kw)
            md()
        except Exception, e:
            print e
            raise # debug
    
    def solr_date(self, dt, kw, key):
        if isinstance(dt, datetime.datetime):
            date = '%sZ' % dt.isoformat()
            kw[key] = date

registerTile('content',
             'templates/revision.pt',
             interface=RevisionAdapter,
             class_=ProtectedContentTile,
             permission='login',
             strict=False)


@tile('addform', interface=RevisionAdapter, permission="view")
class RevisionAddForm(RevisionForm, AddForm):
    
    def save(self, widget, data):
        media = self.model.__parent__.model
        keys = [int(key) for key in media.keys()]
        keys.sort()
        if keys:
            key = str(keys[-1] + 1)
        else:
            key = '0'
        revision = Revision()
        media[key] = revision
        metadata = Metadata()
        revision['metadata'] = metadata
        file = data.fetch('revisionform.data').extracted
        if not file:
            payload = ''
        else:
            if isinstance(file, basestring):
                payload = file
            else:
                payload = file['file'].read()
                metadata.metatype = file['mimetype']
                metadata.filename = file['filename']
        revision['binary'] = Binary(payload=payload)
        metadata.revision = key
        metadata.uid = str(uuid.uuid4())
        metadata.created = timestamp()
        metadata.creator = authenticated_userid(self.request)
        metadata.flag = 'draft'
        metadata.url = '' # calculate tiny url for frontend
        metadata.visibility = data.fetch('revisionform.visibility').extracted
        self.set_metadata_from_form(metadata, data)
        media()
        self.index_metadata_in_solr(self.model.__parent__[key])


@tile('editform', interface=RevisionAdapter, permission="view")
class RevisionEditForm(RevisionForm, EditForm):
    
    def save(self, widget, data):
        metadata = self.model.metadata
        file = data.fetch('revisionform.data').extracted
        if not file:
            payload = ''
        else:
            if isinstance(file, basestring):
                payload = file
            else:
                payload = file['file'].read()
                metadata.metatype = file['mimetype']
                metadata.filename = file['filename']
        self.model.model['binary'].payload = payload
        if not metadata.creator:
            metadata.creator = authenticated_userid(self.request)
        flag = data.fetch('revisionform.flag').extracted
        if flag == 'active' and metadata.flag == 'draft':
            media = self.model.__parent__
            for key in media.keys():
                rev = media[key]
                if rev.metadata.flag == 'active':
                    rev.metadata.flag = 'frozen'
                    rev()
        metadata.flag = flag
        visibility = data.fetch('revisionform.visibility').extracted
        if flag == 'active':
            visibility = 'anonymous'
        metadata.visibility = visibility
        self.set_metadata_from_form(metadata, data)
        self.model()
        self.index_metadata_in_solr(self.model)
