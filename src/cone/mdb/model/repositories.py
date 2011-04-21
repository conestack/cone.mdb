import os
import shutil
from node.locking import locktree
from node.ext.mdb import Repository
from cone.app.model import (
    BaseNode,
    Properties,
    BaseMetadata,
    BaseNodeInfo,
    registerNodeInfo,
)
from cone.mdb.solr import unindex_doc
from cone.mdb.model.utils import (
    solr_config,
    DBLocation,
)
from cone.mdb.model.repository import RepositoryAdapter


class Repositories(BaseNode, DBLocation):
    """Repositories Node.
    """
    
    node_info_name = 'repositories'
    
    @property
    def properties(self):
        if not hasattr(self, '_properties'):
            props = Properties()
            props.in_navtree = True
            self._properties = props
        return self._properties
    
    @property
    def metadata(self):
        if not hasattr(self, '_metadata'):
            metadata = BaseMetadata()
            metadata.title = "Repositories"
            metadata.description = "Container for Repositories"
            self._metadata = metadata
        return self._metadata
    
    def __iter__(self):
        path = self.dbpath
        for repository in os.listdir(path):
            repositorypath = os.path.join(path, repository)
            if os.path.isdir(repositorypath):
                yield repository
    
    iterkeys = __iter__
    
    def __getitem__(self, key):
        try:
            return BaseNode.__getitem__(self, key)
        except KeyError:
            if not key in self.iterkeys():
                raise KeyError(key)
            repositorypath = os.path.join(self.dbpath, key)
            repo = RepositoryAdapter(Repository(repositorypath), key, self)
            self[key] = repo
            return repo
    
    @locktree
    def __delitem__(self, key):
        todelete = self[key]
        if hasattr(self, '_todelete'):
            self._todelete.append(todelete)
        else:
            self._todelete = [todelete]
        BaseNode.__delitem__(self, key)
    
    @locktree
    def __call__(self):
        if not hasattr(self, '_todelete'):
            return
        config = solr_config(self)
        for repository in self._todelete:
            for media in repository.values():
                unindex_doc(config, media)
                for revision in media.values():
                    unindex_doc(config, revision)
            path = os.path.join(self.dbpath, repository.__name__)
            shutil.rmtree(path)
        del self._todelete


info = BaseNodeInfo()
info.title = 'Repositories'
info.description = 'Collection of repositories.'
info.node = Repositories
info.addables = ['repository']
info.icon = 'mdb-static/images/repositories16_16.png'
registerNodeInfo('repositories', info)