from plumber import plumber
from pysolr import Solr as PySolr
from yafowil.base import factory
from cone.tile import (
    Tile,
    tile,
    registerTile,
)
from cone.mdb.model.utils import solr_config
from cone.mdb.model.revision import index_metadata
from cone.app.browser.layout import ProtectedContentTile
from cone.app.browser.form import Form
from cone.app.browser.settings import SettingsPart
from cone.app.browser.utils import make_url
from cone.app.browser.utils import nodepath
from cone.app.browser.ajax import AjaxAction
from cone.mdb.model import Solr


registerTile('content',
             'cone.mdb:browser/templates/solr.pt',
             interface=Solr,
             class_=ProtectedContentTile,
             permission='login')


@tile('rebuild', interface=Solr, permission="manage")
class Rebuild(Tile):
    
    def render(self):
        conf = self.model.attrs
        url = 'http://%s:%s/%s/' % (conf.server, conf.port, conf.basepath)
        PySolr(url).delete(q='*:*')
        repositories = self.model.root['repositories']
        for repository in repositories.values():
            for media in repository.values():
                for revision in media.values():
                    path = '/'.join(nodepath(revision))
                    index_metadata(solr_config(revision), revision.model, path)
        url = make_url(self.request, node=self.model)
        continuation = [AjaxAction(url, 'content', 'inner', '.solr')]
        self.request.environ['cone.app.continuation'] = continuation
        return u''


@tile('editform', interface=Solr, permission="manage")
class SolrSettingsForm(Form):
    __metaclass__ = plumber
    __plumbing__ = SettingsPart
    
    def prepare(self):
        action = make_url(self.request, node=self.model, resource='edit')
        form = factory(
            u'form',
            name='solrform',
            props={
                'action': action,
                'class': 'ajax',
            })
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
        self.form = form
    
    def save(self, widget, data):
        self.model.attrs.server = data.fetch('solrform.server').extracted
        self.model.attrs.port = data.fetch('solrform.port').extracted
        self.model.attrs.basepath = data.fetch('solrform.basepath').extracted
        self.model()