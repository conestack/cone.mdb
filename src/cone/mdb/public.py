from bda.basen import base62
from webob import Response
from cone.app import get_root
from cone.mdb.solr import Metadata
from cone.mdb.model.utils import solr_config
from cone.mdb.model.revision import solr_whitelist


def download(request):
    uid = request.matchdict['uid']
    rev = request.matchdict.get('rev')
    import pdb;pdb.set_trace()
    
    root = get_root()
    config = solr_config(root)
    
    query = 'url:%s' % uid
    if rev:
        query += ' AND revision:%s' % rev
    else:
        query += ' AND flag:active'
    md = Metadata(config, solr_whitelist)
    res = md.query(q=query)
    
    return Response('download')


def search(request):
    term = request.matchdict['term']
    root = get_root()
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
    root = get_root()
    return Response('access')


def info(request):
    root = get_root()
    return Response('info')
