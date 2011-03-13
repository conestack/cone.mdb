from plumber import plumber
from webob.exc import HTTPFound
from yafowil.base import factory
from cone.tile import (
    tile,
    registerTile,
)
from cone.app.browser.ajax import AjaxAction
from cone.app.browser.layout import ProtectedContentTile
from cone.app.browser.form import Form
from cone.app.browser.authoring import EditPart
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
    __plumbing__ = EditPart
    
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
    
    def next(self, request):
        url = make_url(request.request, node=self.model.__parent__)
        if self.ajax_request:
            return AjaxAction(url, 'content', 'inner', '#content')
        return HTTPFound(location=url)
