import os
from plumber import plumber
from cone.tile import (
    tile,
    registerTile,
)
from cone.app.browser.layout import ProtectedContentTile
from cone.app.browser.form import (
    Form,
    YAMLForm,
)
from cone.app.browser.settings import SettingsPart
from cone.mdb.model import Database


registerTile('content',
             'cone.mdb:browser/templates/database.pt',
             interface=Database,
             class_=ProtectedContentTile,
             permission='login')


@tile('editform', interface=Database, permission="manage")
class DatabaseSettingsForm(Form):
    __metaclass__ = plumber
    __plumbing__ = SettingsPart, YAMLForm
    
    action_resource = u'edit'
    form_template_path = os.path.join(os.path.dirname(__file__),
                                      'forms/database.yaml')
    
    def save(self, widget, data):
        self.model.attrs.path = data.fetch('databaseform.path').extracted
        self.model()