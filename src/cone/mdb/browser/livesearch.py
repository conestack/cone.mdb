from cone.app.browser import ajax
from cone.mdb.solr import Metadata
from cone.mdb.browser.utils import solr_config

def solr_livesearch_callback(model, request):
    config = solr_config(model)
    result = list()
    term = request.params['term']
    query = ''
    for search_key in ['title', 'description', 'creator', 'author', 'body']:
        query = '%s%s:%s*~ OR ' % (query, search_key, term)
    query = query.strip(' OR ')
    for md in Metadata(config).query(q=query, fl='title,path'):
        result.append({
            'label': md.title,
            'value': term,
            'target': '/'.join([request.application_url, md.path]),
        })
    return result

ajax.LIVESEARCH_CALLBACK = solr_livesearch_callback