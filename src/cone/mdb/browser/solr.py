from plumber import plumber
from paste.httpexceptions import HTTPFound
from yafowil.base import factory
from cone.tile import (
    tile,
    registerTile,
)
from cone.app.browser.layout import ProtectedContentTile
from cone.app.browser.form import (
    Form,
    EditPart,
)
from cone.app.browser.utils import make_url
from cone.mdb.model import Solr
#from cone.mdb.browser.revision import index_metadata_in_solr


def reindex(root, clear=False):
    # XXX: clear True
    #      speedup by reducing requests to solr
    #      clear root node before iteration
    for rkey in root['repositories'].keys():
        repository = root['repositories'][rkey]
        for mkey in repository.keys():
            media = repository[mkey]
            for revkey in media.keys():
                #index_metadata_in_solr(media[revkey])
                print 'indexed ' + str(media[revkey])

registerTile('content',
             'cone.mdb:browser/templates/solr.pt',
             interface=Solr,
             class_=ProtectedContentTile,
             permission='login',
             strict=False)


@tile('reindexform', interface=Solr, permission="view")
class SolrReindexForm(Form):
    
    def prepare(self):
        form = factory(u'form',
                       name='reindexform',
                       props={'action': self.nodeurl})
        form['clear'] = factory(
            'field:label:checkbox',
            props = {
                'label': 'Clear index?',
                'position': 'inner',
            })
        form['reindex'] = factory(
            'submit',
            props = {
                'action': 'reindex',
                'expression': True,
                'handler': self.reindex,
                'next': self.next,
                'label': 'reindex',
            })
        self.form = form
    
    def reindex(self, widget, data):
        if data.fetch('reindexform.clear').extracted:
            reindex(self.model.root, clear=True)
        else:
            reindex(self.model.root)
    
    def next(self, request):
        url = make_url(request.request, node=self.model)
        return HTTPFound(url)


@tile('editform', interface=Solr, permission="view")
class SolrSettingsForm(Form):
    __metaclass__ = plumber
    __plumbing__ = EditPart
    
    def prepare(self):
        form = factory(u'form',
                       name='editform',
                       props={'action': self.nodeurl})
        form['server'] = factory(
            'field:label:error:text',
            value = self.model.attrs.server,
            props = {
                'required': 'No server given',
                'label': 'Server',
            })
        form['port'] = factory(
            'field:label:error:text',
            value = self.model.attrs.port,
            props = {
                'required': 'No port given',
                'label': 'Port',
            })
        form['basepath'] = factory(
            'field:label:error:text',
            value = self.model.attrs.basepath,
            props = {
                'required': 'No basepath given',
                'label': 'Basepath',
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
    
    def save(self, widget, data):
        self.model.attrs.server = data.fetch('editform.server').extracted
        self.model.attrs.port = data.fetch('editform.port').extracted
        self.model.attrs.basepath = data.fetch('editform.basepath').extracted
        self.model()
