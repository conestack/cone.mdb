import os
import re
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
from cone.app.browser.form import (
    AddForm,
    EditForm,
)
from node.ext.mdb import Repository
from cone.mdb.model import RepositoryAdapter
from cone.mdb.browser.utils import timestamp


registerTile('content',
             'cone.app:browser/templates/listing.pt',
             interface=RepositoryAdapter,
             class_=ProtectedContentTile,
             permission='login',
             strict=False)


class RepositoryForm(object):
    
    @property
    def prepare(self):
        resource='add'
        if self.model.__name__ is not None:
            resource = 'edit'
        action = make_url(self.request, node=self.model, resource=resource)
        form = factory(u'form',
                       name='repositoryform',
                       props={'action': action})
        if self.model.__name__ is None:
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


@tile('addform', interface=RepositoryAdapter, permission="view")
class RepositoryAddForm(RepositoryForm, AddForm):
    
    def save(self, widget, data):
        db = Repository(os.path.join(self.model.__parent__.dbpath,
                        data.fetch('repositoryform.id').extracted))
        repository = RepositoryAdapter(db, None, None)
        metadata = repository.metadata
        metadata.title = data.fetch('repositoryform.title').extracted
        metadata.description = \
            data.fetch('repositoryform.description').extracted
        metadata.creator = authenticated_userid(self.request)
        metadata.created = timestamp()
        repository()


@tile('editform', interface=RepositoryAdapter, permission="view")
class RepositoryEditForm(RepositoryForm, EditForm):
    
    def save(self, widget, data):
        metadata = self.model.metadata
        metadata.title = data.fetch('repositoryform.title').extracted
        metadata.description = \
            data.fetch('repositoryform.description').extracted
        metadata.modified = timestamp()
        self.model()
