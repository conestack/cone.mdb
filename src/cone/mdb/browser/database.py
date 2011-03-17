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
from cone.mdb.model import Database


registerTile('content',
             'cone.mdb:browser/templates/database.pt',
             interface=Database,
             class_=ProtectedContentTile,
             permission='login')


@tile('editform', interface=Database, permission="manage")
class DatabaseSettingsForm(Form):
    __metaclass__ = plumber
    __plumbing__ = SettingsPart
    
    def prepare(self):
        action = make_url(self.request, node=self.model, resource='edit')
        form = factory(
            u'form',
            name='databaseform',
            props={
                'action': action,
            })
        form['path'] = factory(
            'field:label:error:text',
            value = self.model.attrs.path,
            props = {
                'required': 'No path given',
                'label': 'Database directory path',
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
        self.model.attrs.path = data.fetch('databaseform.path').extracted
        self.model()