from plumber import plumber
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
from cone.mdb.model import Amqp
from cone.mdb import amqp


registerTile('content',
             'cone.mdb:browser/templates/amqp.pt',
             interface=Amqp,
             class_=ProtectedContentTile,
             permission='login',
             strict=False)


@tile('editform', interface=Amqp, permission="manage")
class AmqpSettingsForm(Form):
    __metaclass__ = plumber
    __plumbing__ = EditPart
    
    def prepare(self):
        form = factory(u'form',
                       name='amqpform',
                       props={'action': self.nodeurl})
        form['host'] = factory(
            'field:label:error:text',
            value = self.model.attrs.host,
            props = {
                'required': 'No host given',
                'label': 'Host',
            })
        form['user'] = factory(
            'field:label:error:text',
            value = self.model.attrs.user,
            props = {
                'required': 'No user given',
                'label': 'User',
            })
        form['password'] = factory(
            'field:label:error:text',
            value = self.model.attrs.password,
            props = {
                'required': 'No password given',
                'label': 'Password',
            })
        form['ssl'] = factory(
            'field:label:error:text',
            value = self.model.attrs.ssl,
            props = {
                'required': 'Either True or False',
                'label': 'SSL',
            })
        form['exchange'] = factory(
            'field:label:error:text',
            value = self.model.attrs.exchange,
            props = {
                'required': 'No exchange given',
                'label': 'Exchange',
            })
        form['queue'] = factory(
            'field:label:error:text',
            value = self.model.attrs.queue,
            props = {
                'required': 'No queue given',
                'label': 'Queue',
            })
        form['type'] = factory(
            'field:label:error:text',
            value = self.model.attrs.type,
            props = {
                'required': 'No type given',
                'label': 'Type',
            })
        form['realm'] = factory(
            'field:label:error:text',
            value = self.model.attrs.realm,
            props = {
                'required': 'No realm given',
                'label': 'Realm',
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
        def id(name):
            return 'editform.%s' % name
        self.model.attrs.host = data.fetch(id('host')).extracted
        self.model.attrs.user = data.fetch(id('user')).extracted
        self.model.attrs.password = data.fetch(id('password')).extracted
        self.model.attrs.ssl = data.fetch(id('ssl')).extracted
        self.model.attrs.exchange = data.fetch(id('exchange')).extracted
        self.model.attrs.queue = data.fetch(id('queue')).extracted
        self.model.attrs.type = data.fetch(id('type')).extracted
        self.model.attrs.realm = data.fetch(id('realm')).extracted
        self.model()
        amqp.consumer = amqp.create_consumer()
