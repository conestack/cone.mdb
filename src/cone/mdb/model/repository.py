import os
from node.locking import locktree
from node.ext.mdb import Repository
from pyramid.security import authenticated_userid
from cone.app.model import (
    Properties,
    XMLProperties,
    AdapterNode,
    NodeInfo,
    registerNodeInfo,
)
from cone.mdb.solr import unindex_doc
from cone.mdb.model.media import MediaAdapter
from cone.mdb.model.utils import (
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
    
    node_info_name = 'repository'
    
    @property
    def properties(self):
        if not hasattr(self, '_properties'):
            props = Properties()
            props.in_navtree = True
            props.editable = True
            props.deletable = True
            props.action_up = True
            self._properties = props
        return self._properties
    
    @property
    def metadata(self):
        if hasattr(self, '_metadata'):
            return self._metadata
        if self.model.__name__ is not None:
            path = os.path.join(self.model.__name__, 'database.info')
            self._metadata = XMLProperties(path)
            return self._metadata
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