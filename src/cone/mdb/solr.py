import types
from lxml import etree
from pysolr import Solr

class Config(object):
    
    def __init__(self):
        self.server = 'localhost'
        self.port = '8983'
        self.path = 'solr'

class Metadata(dict):
    
    attributes = [
        'uid',
        'author',
        'created',
        'effective',
        'expires',
        'revision',
        'metatype',
        'creator',
        'keywords',
        'url',
        'relations',
        'title',
        'description',
        'alttag',
        'body',
        'flag',
        'visibility',
        'path',
        'modified',
        'filename',
    ]
    
    def __init__(self, config, **kwargs):
        object.__setattr__(self, 'config', config)
        for arg in kwargs.keys():
            if arg in object.__getattribute__(self, 'attributes'):
                self[arg] = kwargs[arg]
            else:
                raise AttributeError(u"'%s' is not a valid attribute" % arg)
    
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if not name in object.__getattribute__(self, 'attributes'):
            raise AttributeError(u"'%s' is not a valid attribute" % name)
        self[name] = value
    
    def __call__(self):
        self.solr().add([self])
    
    def query(self, q=None, **kw):
        if q is None:
            res = self.solr().search('uid:%s' % self.uid)
            if not res:
                raise KeyError(u"Entry with uid %s does not exist" % self.uid)
            res = [r for r in res]
            for key, value in res[0].items():
                self[key] = value
        else:
            config = object.__getattribute__(self, 'config')
            res = self.solr().search(q, **kw)
            ret = list()
            for r in res:
                ret.append(Metadata(config, **r))
            return ret
    
    def as_xml(self):
        root = etree.Element('metadata')
        for key, value in self.items():
            sub = etree.SubElement(root, key)
            if type(value) in [types.ListType, types.TupleType]:
                for item in value:
                    subsub = etree.SubElement(sub, 'item')
                    subsub.text = item
            else:
                sub.text = unicode(value)
        return root
    
    def solr(self):
        try:
            return object.__getattribute__(self, '_solr')
        except AttributeError, e:
            cfg = object.__getattribute__(self, 'config')
            solr = Solr('http://%s:%s/%s' % (cfg.server, cfg.port, cfg.path))
            object.__setattr__(self, '_solr', solr)
            return solr