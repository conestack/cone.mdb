from pyramid.security import authenticated_userid
from cone.app.browser import ajax
from cone.mdb.solr import Metadata
from cone.mdb.model import solr_config
from cone.mdb.model.revision import solr_whitelist

def solr_livesearch_callback(model, request):
    result = list()
    if not authenticated_userid(request):
        return result
    config = solr_config(model)
    term = request.params['term']
    query = ''
    for search_key in ['title', 'description', 'creator', 'author', 'body']:
        query = '%s%s:%s*~ OR ' % (query, search_key, term)
    query = query.strip(' OR ')
    for md in Metadata(config, solr_whitelist).query(q=query, fl='title,path'):
        result.append({
            'label': md.title,
            'value': term,
            'target': '/'.join([request.application_url, md.path]),
        })
    return result

ajax.LIVESEARCH_CALLBACK = solr_livesearch_callback