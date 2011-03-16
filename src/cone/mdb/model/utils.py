import os
import datetime
from cone.app import APP_PATH
from cone.app.model import ConfigProperties
from cone.mdb.solr import Config


def timestamp():
    return datetime.datetime.now()


def solr_config(model):
    settings = model.root['settings']['solr']
    config = Config()
    config.server = settings.attrs.server
    config.port = settings.attrs.port
    config.path = settings.attrs.basepath
    return config


class DBLocation(object):
    
    @property
    def dbpath(self):
        path = os.path.join(APP_PATH , 'etc', 'database.cfg')
        config = ConfigProperties(path)
        path = config.path
        if not os.path.isabs(path):
            path = os.path.sep.join([APP_PATH, path])
        return path