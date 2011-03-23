import types
from lxml import etree
from pysolr import Solr

class Config(object):
    
    def __init__(self):
        self.server = 'localhost'
        self.port = '8983'
        self.path = 'solr'


class QueryError(Exception): pass


class Group(object):
    
    def __init__(self, term):
        self.term = term
    
    def __and__(self, term):
        self.term.query = '(%s)' % self.term.query
        return self.term & term
    
    def __or__(self, term):
        self.term.query = '(%s)' % self.term.query
        return self.term | term


class Term(object):
    
    def __init__(self, name, value):
        self.query = ''
        self.name = name
        self.value = value
    
    def __str__(self):
        return self.query
    
    __repr__ = __str__
    
    def __and__(self, term):
        self.extend(term, 'AND')
        return self
    
    def __or__(self, term):
        self.extend(term, 'OR')
        return self
    
    def extend(self, term, operator):
        if isinstance(term, Group):
            if self.query:
                self.query = '%s %s (%s)' % (
                    self.query, operator, term.term)
            else:
                self.query = '%s:%s %s (%s)' % (
                    self.name, self.value, operator, term.term)
            return
        if self.query:
            self.query = '%s %s %s:%s' % (
                self.query, operator, term.name, term.value)
        else:
            self.query = '%s:%s %s %s:%s' % (
                self.name, self.value, operator, term.name, term.value)
        term.query = self.query


class Metadata(dict):
    
    def __init__(self, config, attributes, **kwargs):
        object.__setattr__(self, 'config', config)
        object.__setattr__(self, 'attributes', attributes)
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
            attributes = object.__getattribute__(self, 'attributes')
            res = self.solr().search(q, **kw)
            ret = list()
            for r in res:
                ret.append(Metadata(config, attributes, **r))
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
        except AttributeError:
            cfg = object.__getattribute__(self, 'config')
            solr = Solr('http://%s:%s/%s' % (cfg.server, cfg.port, cfg.path))
            object.__setattr__(self, '_solr', solr)
            return solr