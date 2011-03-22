from webob import Response
from cone.app import get_root
from cone.mdb.solr import Metadata
from cone.mdb.model.utils import solr_config
from cone.mdb.model.revision import solr_whitelist


class MDBError(Exception): pass


def download(request):
    uid = request.matchdict['uid']
    rev = request.matchdict.get('rev')
    root = get_root(None)
    config = solr_config(root)
    query = 'url:%s' % uid
    if rev:
        query += ' AND revision:%s' % rev
    else:
        query += ' AND flag:active'
    md = Metadata(config, solr_whitelist)
    result = md.query(q=query)
    if len(result) != 1:
        raise MDBError(u'Dataset not found in SOLR')
    physical_path = u'/xsendfile%s.binary' % result[0]['physical_path']
    response = Response()
    response.content_type = result[0]['metatype']
    response.content_disposition = 'attachment'
    response.headers.add('X-Accel-Redirect', physical_path)
    return response


def search(request):
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
