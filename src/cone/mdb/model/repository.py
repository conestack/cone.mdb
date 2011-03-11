import os
from cone.app.model import (
    Properties,
    XMLProperties,
    AdapterNode,
    BaseNodeInfo,
    registerNodeInfo,
)
from cone.mdb.model.media import MediaAdapter
from cone.mdb.model.utils import DBLocation


class RepositoryAdapter(AdapterNode, DBLocation):
    
    node_info_name = 'repository'
    
    @property
    def properties(self):
        props = Properties()
        props.in_navtree = True
        props.editable = True
        props.action_up = True
        return props
    
    @property
    def metadata(self):
        if hasattr(self, '_metadata'):
            return self._metadata
        if self.model.__name__ is not None:
            path = os.path.join(self.model.__name__, 'database.info')
            self._metadata = XMLProperties(path)
            return self._metadata
        return Properties()
    
    def __getitem__(self, name):
        try:
            return AdapterNode.__getitem__(self, name)
        except KeyError:
            if not name in self.iterkeys():
                raise KeyError(name)
            media = MediaAdapter(self.model[name], name, self)
            self[name] = media
            return media
    
    def __call__(self):
        self.model()
        self.metadata()


info = BaseNodeInfo()
info.title = 'Repository'
info.description = 'A repository.'
info.node = RepositoryAdapter
info.addables = ['media']
registerNodeInfo('repository', info)