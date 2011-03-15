import os
from cone.app import APP_PATH
from cone.app.model import BaseNode
from cone.app.model import ConfigProperties
from cone.app.security import DEFAULT_SETTINGS_ACL


class Amqp(BaseNode):
    __acl__ = DEFAULT_SETTINGS_ACL
    
    def __init__(self, name=None):
        BaseNode.__init__(self, name)
        path = os.path.join(APP_PATH, 'etc', 'amqp.cfg')
        self._config = ConfigProperties(path)
    
    def __call__(self):
        self.attrs()
    
    @property
    def attrs(self):
        return self._config
    
    @property
    def amqpstatus(self):
        from zamqp import runner
        if runner.event_consumer and runner.event_consumer.isAlive():
            return 'OK'
        return 'Failed'
