import os
import shutil
from cone.app.model import (
    BaseNode,
    Properties,
    BaseMetadata,
    BaseNodeInfo,
    registerNodeInfo,
)
from node.ext.mdb import Repository
from cone.mdb.model.utils import DBLocation
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
    
    def __delitem__(self, key):
        BaseNode.__delitem__(self, key)
        repositorypath = os.path.join(self.dbpath, key)
        shutil.rmtree(repositorypath)
    
    def __call__(self):
        pass


info = BaseNodeInfo()
info.title = 'Repositories'
info.description = 'Collection of repositories.'
info.node = Repositories
info.addables = ['repository']
info.icon = 'mdb-static/images/repositories16_16.png'
registerNodeInfo('repositories', info)