import time
import datetime
from webob import Response
from cone.app import get_root
from cone.mdb.solr import Metadata
from cone.mdb.model.utils import solr_config
from cone.mdb.model.revision import solr_whitelist


class MDBError(Exception): pass


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


def solr2dt(val):
    # val: '2011-03-03T00:00:00Z'
    format = '%Y-%m-%dT%H:%M:%SZ'
    args = time.strptime(val, format)[0:3] + (0, 0, 0)
    return datetime.datetime(*args)


def download(request):
    uid = request.matchdict['uid']
    rev = request.matchdict.get('rev')
    root = get_root(None)
    config = solr_config(root)
    query = Term('url', uid)
    if rev:
        query = query & Term('revision', rev)
    else:
        query = query & Term('flag', 'active')
    query = query & Term('visibility', 'anonymous')
    md = Metadata(config, solr_whitelist)
    result = md.query(q=query)
    if len(result) != 1:
        raise MDBError(u'Dataset not found in SOLR. Query: %s' % query)
    now = datetime.datetime.now()
    effective = result[0].get('effective')
    if effective and solr2dt(effective) > now:
        raise MDBError(u'Item not effective')
    expires = result[0].get('expires')
    if expires and solr2dt(expires) < now:
        raise MDBError(u'Item expired')
    physical_path = u'/xsendfile%s.binary' % result[0]['physical_path']
    response = Response()
    response.content_type = result[0]['metatype']
    response.content_disposition = 'attachment'
    response.headers.add('X-Accel-Redirect', physical_path)
    return response


def search(request):
    """
    title: String
    description
    repository: String
    uid: String (base62)
    revision (dict):
        revid: String
        title: String
        description: String
        mimetype: String
        filename: String
        size: int
        alttag: String 
    """
    term = request.matchdict['term']
    root = get_root(None)
    config = solr_config(root)
    query = ''
    for search_key in ['title', 'description', 'creator', 'author', 'body']:
        query = '%s%s:%s*~ OR ' % (query, search_key, term)
    query = query.strip(' OR ')
    result = list()
    for md in Metadata(config, solr_whitelist).query(q=query, fl='title,path'):
        result.append({
            'label': md.title,
        })
    return result


def access(request):
    root = get_root(None)
    return Response('access')


def info(request):
    root = get_root(None)
    return Response('info')
