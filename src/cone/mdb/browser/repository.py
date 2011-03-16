import re
from plumber import plumber
from pyramid.security import authenticated_userid
from yafowil.base import (
    factory,
    ExtractionError,
)
from cone.tile import (
    tile,
    registerTile,
)
from cone.app.browser.utils import make_url
from cone.app.browser.layout import ProtectedContentTile
from cone.app.browser.form import Form
from cone.app.browser.authoring import (
    AddPart,
    EditPart,
)
from node.ext.mdb import Repository
from cone.mdb.model import (
    RepositoryAdapter,
    add_repository,
    update_repository,
)


registerTile('content',
             'cone.app:browser/templates/listing.pt',
             interface=RepositoryAdapter,
             class_=ProtectedContentTile,
             permission='login',
             strict=False)


class RepositoryForm(object):
    
    def prepare(self):
        resource = self.action_resource
        action = make_url(self.request, node=self.model, resource=resource)
        form = factory(
            u'form',
            name = 'repositoryform',
            props = {
                'action': action,
            })
        if resource == 'add':
            form['id'] = factory(
                'field:label:*valid_id:error:text',
                props = {
                    'required': 'No repository id given',
                    'label': 'Repository id',
                },
                custom = {
                    'valid_id': ([self.valid_id], [], [], []),
                })
        form['title'] = factory(
            'field:label:error:text',
            value = self.model.metadata.title,
            props = {
                'required': 'No media title given',
                'label': 'Repository title',
            })
        form['description'] = factory(
            'field:label:error:richtext',
            value = self.model.metadata.description,
            props = {
                'label': 'Repository description',
                'rows': 5,
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
    
    def valid_id(self, widget, data):
        id = self.request.params.get('repositoryform.id')
        if id and not re.match('^[a-zA-Z0-9]', id):
            raise ExtractionError(u'Id contains illegal characters')
        if id in self.model.keys():
            raise ExtractionError(u'Repository "%s" already exists' % id)
        return id


@tile('addform', interface=RepositoryAdapter, permission="add")
class RepositoryAddForm(RepositoryForm, Form):
    __metaclass__ = plumber
    __plumbing__ = AddPart
    
    def save(self, widget, data):
        add_repository(
            self.request,
            self.model.__parent__,
            data.fetch('repositoryform.id').extracted,
            data.fetch('repositoryform.title').extracted,
            data.fetch('repositoryform.description').extracted)


@tile('editform', interface=RepositoryAdapter, permission="edit")
class RepositoryEditForm(RepositoryForm, Form):
    __metaclass__ = plumber
    __plumbing__ = EditPart
    
    def save(self, widget, data):
        update_repository(
            self.request,
            self.model,
            data.fetch('repositoryform.title').extracted,
            data.fetch('repositoryform.description').extracted)