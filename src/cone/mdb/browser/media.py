from plumber import plumber
from pyramid.security import authenticated_userid
from yafowil.base import factory
from bda.basen import base62
from cone.tile import (
    tile,
    render_tile,
)
from cone.app.browser.utils import make_url
from cone.app.browser.layout import ProtectedContentTile
from cone.app.browser.form import Form
from cone.app.browser.authoring import (
    AddPart,
    EditPart,
)
from node.ext.mdb import (
    Media,
    MediaKeys,
)
from cone.mdb.model import (
    MediaAdapter,
    add_media,
    update_media,
)


@tile('content',
      'templates/media.pt',
      interface=MediaAdapter,
      permission='login')


class MediaTile(ProtectedContentTile):
    
    @property
    def active_revision(self):
        revision = self.model.active_revision
        if revision is not None:
            return render_tile(revision, self.request, 'revisiondetails')


class MediaForm(object):
    
    def prepare(self):
        resource = self.action_resource
        action = make_url(self.request, node=self.model, resource=resource)
        form = factory(
            u'form',
            name = 'mediaform',
            props = {
                'action': action,
            })
        form['title'] = factory(
            'field:label:error:text',
            value = self.model.metadata.title,
            props = {
                'required': 'No media title given',
                'label': 'Media title',
            })
        form['description'] = factory(
            'field:label:error:textarea',
            value = self.model.metadata.description,
            props = {
                'label': 'Media description',
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


@tile('addform', interface=MediaAdapter, permission="add")
class MediaAddForm(MediaForm, Form):
    __metaclass__ = plumber
    __plumbing__ = AddPart
    
    def save(self, widget, data):
        add_media(
            self.request,
            self.model.__parent__,
            data.fetch('mediaform.title').extracted,
            data.fetch('mediaform.description').extracted)


@tile('editform', interface=MediaAdapter, permission="edit")
class MediaEditForm(MediaForm, Form):
    __metaclass__ = plumber
    __plumbing__ = EditPart
    
    def save(self, widget, data):
        update_media(
            self.request,
            self.model,
            data.fetch('mediaform.title').extracted,
            data.fetch('mediaform.description').extracted)