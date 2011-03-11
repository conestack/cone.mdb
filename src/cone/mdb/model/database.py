import os
from cone.app import APP_PATH
from cone.app.model import BaseNode
from cone.app.model import ConfigProperties
from cone.app.security import DEFAULT_SETTINGS_ACL


class Database(BaseNode):
    __acl__ = DEFAULT_SETTINGS_ACL
    
    def __init__(self, name=None):
        BaseNode.__init__(self, name)
        path = os.path.join(APP_PATH, 'etc', 'database.cfg')
        self._config = ConfigProperties(path)
    
    def __call__(self):
        self.attrs()
    
    @property
    def attrs(self):
        return self._config
    
    @property
    def abspath(self):
        path = self.attrs.path
        if not path:
            return ''
        if not os.path.abspath(path):
            path = os.path.sep.join([APP_PATH, path])
        return path
    
    @property
    def dbstatus(self):
        path = self.abspath
        if not os.path.exists(path):
            return 'Database path not exists - "%s"' % path
        return 'OK'
