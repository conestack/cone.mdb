import os
from cone.app.model import (
    Properties,
    XMLProperties,
    AdapterNode,
    BaseNodeInfo,
    registerNodeInfo,
)
from cone.mdb.model.revision import RevisionAdapter


class MediaAdapter(AdapterNode):
    
    node_info_name = 'media'
    
    @property
    def properties(self):
        props = Properties()
        props.in_navtree = False
        props.editable = True
        props.action_up = True
        props.action_view = True
        props.action_list = True
        return props
    
    @property
    def metadata(self):
        if hasattr(self, '_metadata'):
            return self._metadata
        if self.model.__name__ is not None:
            path = os.path.join(self.model.root.__name__,
                                *self.model.mediapath + ['media.info'])
            self._metadata = XMLProperties(path)
            return self._metadata
        return Properties()
    
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