from plumber import plumber
from yafowil.base import factory
from cone.tile import (
    tile,
    registerTile,
)
from cone.app.browser.layout import ProtectedContentTile
from cone.app.browser.form import Form
from cone.app.browser.settings import SettingsPart
from cone.app.browser.utils import make_url
from cone.mdb.model import Solr


registerTile('content',
             'cone.mdb:browser/templates/solr.pt',
             interface=Solr,
             class_=ProtectedContentTile,
             permission='login')


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