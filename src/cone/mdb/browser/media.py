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
from cone.app.browser.form import (
    Form,
    AddPart,
    EditPart,
)
from node.ext.mdb import (
    Media,
    MediaKeys,
)
from cone.mdb.model import MediaAdapter
from cone.mdb.browser.utils import timestamp


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
        resource='add'
        if self.model.__name__ is not None:
            resource = 'edit'
        action = make_url(self.request, node=self.model, resource=resource)
        form = factory(u'form',
                       name='mediaform',
                       props={'action': action})
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
        keys = MediaKeys(self.model.__parent__.model.__name__)
        key = keys.next()
        keys.dump(key)
        db = self.model.__parent__.model
        db[key] = Media()
        media = MediaAdapter(db[key], None, None)
        media.metadata.title = data.fetch('mediaform.title').extracted
        media.metadata.description = \
            data.fetch('mediaform.description').extracted
        media.metadata.creator = authenticated_userid(self.request)
        media.metadata.created = timestamp()
        media()


@tile('editform', interface=MediaAdapter, permission="edit")
class MediaEditForm(MediaForm, Form):
    __metaclass__ = plumber
    __plumbing__ = EditPart
    
    def save(self, widget, data):
        metadata = self.model.metadata
        metadata.title = data.fetch('mediaform.title').extracted
        metadata.description = \
            data.fetch('mediaform.description').extracted
        metadata.modified = timestamp()
        self.model()
