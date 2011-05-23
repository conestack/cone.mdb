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
from cone.mdb.model import Amqp


registerTile('content',
             'cone.mdb:browser/templates/amqp.pt',
             interface=Amqp,
             class_=ProtectedContentTile,
             permission='login')


@tile('editform', interface=Amqp, permission="manage")
class AmqpSettingsForm(Form):
    __metaclass__ = plumber
    __plumbing__ = SettingsPart, YAMLForm
    
    action_resource = u'edit'
    form_template_path = os.path.join(os.path.dirname(__file__),
                                      'forms/amqp.yaml')
    
    def save(self, widget, data):
        def id(name):
            return 'amqpform.%s' % name
        self.model.attrs.host = data.fetch(id('host')).extracted
        self.model.attrs.user = data.fetch(id('user')).extracted
        self.model.attrs.password = data.fetch(id('password')).extracted
        self.model.attrs.ssl = data.fetch(id('ssl')).extracted
        self.model.attrs.exchange = data.fetch(id('exchange')).extracted
        self.model.attrs.queue = data.fetch(id('queue')).extracted
        self.model.attrs.type = data.fetch(id('type')).extracted
        self.model.attrs.realm = data.fetch(id('realm')).extracted
        self.model()