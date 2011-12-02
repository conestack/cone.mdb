import os
from plumber import plumber
from node.locking import locktree
from node.utils import instance_property
from node.ext.mdb import Repository
from pyramid.security import authenticated_userid
from cone.app.model import (
    Properties,
    ProtectedProperties,
    XMLProperties,
    AdapterNode,
    NodeInfo,
    registerNodeInfo,
)
from cone.app.security import DEFAULT_NODE_PROPERTY_PERMISSIONS
from cone.mdb.solr import unindex_doc
from cone.mdb.model.media import MediaAdapter
from cone.mdb.model.utils import (
    GroupToRepositoryACL,
    DBLocation,
    timestamp,
    solr_config,
)

def add_repository(request, repositories, id, title, description):
    """Create and add repository.
    
    ``request``
        webob request
    ``repositories``
        cone.mdb.model.Repositories
    ``id``
        new repository id
    ``title``
        repository title
    ``description``
        repository description
    """
    model = Repository(os.path.join(repositories.dbpath, id))
    repository = RepositoryAdapter(model, None, None)
    metadata = repository.metadata
    metadata.title = title
    metadata.description = description
    metadata.creator = authenticated_userid(request)
    metadata.created = timestamp()
    repository()
    return repository


def update_repository(request, repository, title, description):
    """Update existing repository.
    
    ``repository``
        cone.mdb.model.RepositoryAdapter
    ``title``
        new title
    ``description``
        new description
    """
    metadata = repository.metadata
    metadata.title = title
    metadata.description = description
    metadata.modified = timestamp()
    metadata.modified_by = authenticated_userid(request)
    repository()


class RepositoryAdapter(AdapterNode, DBLocation):
    __metaclass__ = plumber
    __plumbing__ = GroupToRepositoryACL
    
    node_info_name = 'repository'
    
    @instance_property
    def properties(self):
        props = ProtectedProperties(self, DEFAULT_NODE_PROPERTY_PERMISSIONS)
        props.in_navtree = True
        props.action_edit = True
        props.action_delete = True
        props.action_up = True
        return props
    
    @instance_property
    def metadata(self):
        if self.model.__name__ is not None:
            path = os.path.join(self.model.__name__, 'database.info')
            return XMLProperties(path)
        return Properties()                                 #pragma NO COVERAGE
    
    def __getitem__(self, key):
        try:
            return AdapterNode.__getitem__(self, key)
        except KeyError:
            if not key in self.iterkeys():
                raise KeyError(key)
            media = MediaAdapter(self.model[key], key, self)
            self[key] = media
            return media
    
    @locktree
    def __delitem__(self, key):
        todelete = self[key]
        if hasattr(self, '_todelete'):
            self._todelete.append(todelete)
        else:
            self._todelete = [todelete]
        AdapterNode.__delitem__(self, key)
    
    @locktree
    def __call__(self):
        if hasattr(self, '_todelete'):
            config = solr_config(self)
            for media in self._todelete:
                unindex_doc(config, media)
                for revision in media.values():
                    unindex_doc(config, revision)
                path = os.path.join(self.model.__name__,
                                    *media.model.mediapath + ['media.info'])
                os.remove(path)
                del self.model[media.__name__]
            del self._todelete
        self.model()
        self.metadata()


info = NodeInfo()
info.title = 'Repository'
info.description = 'A repository.'
info.node = RepositoryAdapter
info.addables = ['media']
info.icon = 'mdb-static/images/repository16_16.png'
registerNodeInfo('repository', info)