import os
from cone.app import APP_PATH
from cone.app.model import ConfigProperties


class DBLocation(object):
    
    @property
    def dbpath(self):
        path = os.path.join(APP_PATH , 'etc', 'database.cfg')
        config = ConfigProperties(path)
        path = config.path
        if not os.path.isabs(path):
            path = os.path.sep.join([APP_PATH, path])
        return path
