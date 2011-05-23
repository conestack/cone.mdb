import os
import re
from plumber import plumber
from yafowil.base import (
    ExtractionError,
)
from cone.tile import (
    tile,
    registerTile,
)
from cone.app.browser.layout import ProtectedContentTile
from cone.app.browser.form import (
    Form,
    YAMLForm,
)
from cone.app.browser.authoring import (
    AddPart,
    EditPart,
)
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
    __metaclass__ = plumber
    __plumbing__ = YAMLForm
    
    form_template_path = os.path.join(os.path.dirname(__file__),
                                      'forms/repository.yaml')
    
    def id_mode(self, widget, data):
        return self.action_resource == 'add' and 'edit' or None
    
    def valid_id(self, widget, data):
        id = self.request.params.get('repositoryform.id')
        if id and not re.match('^[a-zA-Z0-9]', id):
            raise ExtractionError(u'Id contains illegal characters')
        if id in self.model.__parent__.keys():
            raise ExtractionError(u'Repository "%s" already exists' % id)
        return id


@tile('addform', interface=RepositoryAdapter, permission="add")
class RepositoryAddForm(RepositoryForm, Form):
    __metaclass__ = plumber
    __plumbing__ = AddPart
    
    def save(self, widget, data):
        self.model.__name__ = data.fetch('repositoryform.id').extracted
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