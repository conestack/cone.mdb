import os
from plumber import plumber
from cone.tile import (
    tile,
    render_tile,
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
    __metaclass__ = plumber
    __plumbing__ = YAMLForm
    
    form_template_path = os.path.join(os.path.dirname(__file__),
                                      'forms/media.yaml')


@tile('addform', interface=MediaAdapter, permission="add")
class MediaAddForm(MediaForm, Form):
    __metaclass__ = plumber
    __plumbing__ = AddPart
    
    def save(self, widget, data):
        media = add_media(
            self.request,
            self.model.__parent__,
            data.fetch('mediaform.title').extracted,
            data.fetch('mediaform.description').extracted)
        self.model.__name__ = media.__name__


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