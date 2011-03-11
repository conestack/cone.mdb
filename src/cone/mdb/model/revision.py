from cone.app.model import (
    Properties,
    AdapterNode,
    BaseNodeInfo,
    registerNodeInfo,
)


class RevisionAdapter(AdapterNode):
    
    node_info_name = 'revision'
    
    @property
    def properties(self):
        props = Properties()
        props.in_navtree = True
        flag = self.metadata.flag
        props.editable = flag == 'draft' and True or False
        props.action_up = True
        props.action_view = True
        return props
    
    @property
    def metadata(self):
        if self.model:
            return self.model['metadata']
        return Properties()
    
    def __iter__(self):
        return iter(list())
    
    iterkeys = __iter__
    
    def __call__(self):
        self.model()


info = BaseNodeInfo()
info.title = 'Revision'
info.description = 'A revision.'
info.node = RevisionAdapter
info.addables = []
registerNodeInfo('revision', info)