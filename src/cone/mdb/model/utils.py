import os
import datetime
from plumber import (
    Part,
    extend,
)
from pyramid.security import (
    Everyone,
    Allow,
    Deny,
    ALL_PERMISSIONS,
)
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


class GroupToRepositoryACL(Part):
    
    @extend
    @property
    def __acl__(self):
        node = self
        while node and node.node_info_name != 'repository':
            # XXX: hack against node_info_name
            #      quick solution due to recursive imports
            node = node.parent
        return [
            (Allow, 'group:%s' % node.name, ['view', 'add', 'edit']),
            (Allow, 'role:owner', ['view', 'add', 'edit', 'delete']),
            (Allow, 'role:manager', ['view', 'add', 'edit', 'delete', 'manage']),
            (Allow, Everyone, ['login']),
            (Deny, Everyone, ALL_PERMISSIONS),
        ]