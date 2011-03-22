import os
from pysolr import Solr as PySolr
from cone.app import APP_PATH
from cone.app.model import BaseNode
from cone.app.model import ConfigProperties
from cone.app.security import DEFAULT_SETTINGS_ACL


class Solr(BaseNode):
    __acl__ = DEFAULT_SETTINGS_ACL
    
    def __init__(self, name=None):
        BaseNode.__init__(self, name)
        path = os.path.join(APP_PATH, 'etc', 'solr.cfg')
        self._config = ConfigProperties(path)
    
    def __call__(self):
        self.attrs()
    
    @property
    def attrs(self):
        return self._config
    
    @property
    def status(self):
        try:
            conf = self.attrs
            url = 'http://%s:%s/%s/' % (conf.server, conf.port, conf.basepath)
            PySolr(url).search(q='uid:inexistent')
            return 'OK'
        except Exception:
            return 'Failed'