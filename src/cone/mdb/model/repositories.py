import os
from cone.app.model import (
    BaseNode,
    Properties,
    BaseMetadata,
    BaseNodeInfo,
    registerNodeInfo,
)
from node.ext.mdb import Repository
from cone.mdb.model.repository import RepositoryAdapter
from cone.mdb.model.utils import DBLocation


class Repositories(BaseNode, DBLocation):
    """Repositories Node.
    """
    
    node_info_name = 'repositories'
    
    @property
    def properties(self):
        props = Properties()
        props.in_navtree = True
        props.editable = False
        return props
    
    @property
    def metadata(self):
        metadata = BaseMetadata()
        metadata.title = "Repositories"
        metadata.description = "Your repositories"
        return metadata
    
    def __iter__(self):
        # XXX: filter by group memebership of user if not manager
        path = self.dbpath
        for repository in os.listdir(path):
            repositorypath = os.path.join(path, repository)
            if os.path.isdir(repositorypath):
                yield repository
    
    iterkeys = __iter__
    
    def __getitem__(self, name):
        try:
            return BaseNode.__getitem__(self, name)
        except KeyError:
            if not name in self.iterkeys():
                raise KeyError(name)
            repositorypath = os.path.join(self.dbpath, name)
            repo = RepositoryAdapter(Repository(repositorypath), name, self)
            self[name] = repo
            return repo


info = BaseNodeInfo()
info.title = 'Repositories'
info.description = 'Collection of repositories.'
info.node = Repositories
info.addables = ['repository']
info.in_navtree = True
registerNodeInfo('repositories', info)