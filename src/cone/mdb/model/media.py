import os
import uuid
from pyramid.security import authenticated_userid
from node.ext.mdb import (
    Media,
    MediaKeys,
)
from cone.app.model import (
    Properties,
    XMLProperties,
    AdapterNode,
    BaseNodeInfo,
    registerNodeInfo,
)
from cone.mdb.model.revision import RevisionAdapter
from cone.mdb.model.utils import timestamp


def add_media(request, repository, title, description):
    """Create and add media.
    
    ``request``
        webob request
    ``repository``
        cone.mdb.model.RepositoryAdapter
    ``title``
        repository title
    ``description``
        repository description
    """
    keys = MediaKeys(repository.model.__name__)
    key = keys.next()
    keys.dump(key)
    repository = repository.model
    model = Media()
    repository[key] = model
    media = MediaAdapter(model, None, None)
    media.metadata.uid = str(uuid.uuid4())
    media.metadata.title = title
    media.metadata.description = description
    media.metadata.creator = authenticated_userid(request)
    media.metadata.created = timestamp()
    media()


def update_media(request, media, title, description):
    """Update existing media.
    
    ``media``
        cone.mdb.model.MediaAdapter
    ``title``
        new title
    ``description``
        new description
    """
    metadata = media.metadata
    metadata.title = title
    metadata.description = description
    metadata.modified = timestamp()
    metadata.modified_by = authenticated_userid(request)
    media()


class MediaAdapter(AdapterNode):
    
    node_info_name = 'media'
    
    @property
    def properties(self):
        if not hasattr(self, '_properties'):
            props = Properties()
            props.in_navtree = True
            props.editable = True
            props.action_up = True
            props.action_view = True
            props.action_list = True
            self._properties = props
        return self._properties
    
    @property
    def metadata(self):
        if hasattr(self, '_metadata'):
            return self._metadata
        if self.model.__name__ is not None:
            path = os.path.join(self.model.root.__name__,
                                *self.model.mediapath + ['media.info'])
            self._metadata = XMLProperties(path)
            return self._metadata
        return Properties()                                 #pragma NO COVERAGE
    
    @property
    def active_revision(self):
        for key in self.keys():
            if self[key].metadata.flag == 'active':
                return self[key]
    
    def __getitem__(self, name):
        try:
            return AdapterNode.__getitem__(self, name)
        except KeyError:
            if not name in self.iterkeys():
                raise KeyError(name)
            revision = RevisionAdapter(self.model[name], name, self)
            self[name] = revision
            return revision
    
    def __call__(self):
        self.model()
        self.metadata()


info = BaseNodeInfo()
info.title = 'Media'
info.description = 'A media object.'
info.node = MediaAdapter
info.addables = ['revision']
registerNodeInfo('media', info)