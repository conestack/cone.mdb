from pyramid.security import authenticated_userid
from cone.app.browser import ajax
from cone.mdb.solr import Metadata
from cone.mdb.model import solr_config
from cone.mdb.solr import (
    Term,
    SOLR_FIELDS,
)

def solr_livesearch_callback(model, request):
    result = list()
    if not authenticated_userid(request):
        return result
    config = solr_config(model)
    term = request.params['term']
    s_term = '%s*~' % term
    query = Term('title', s_term) \
          | Term('description', s_term) \
          | Term('creator', s_term) \
          | Term('author', s_term) \
          | Term('body', s_term)
    for md in Metadata(config, SOLR_FIELDS).query(q=query, fl='title,path'):
        result.append({
            'label': md.title,
            'value': term,
            'target': '/'.join([request.application_url, md.path]),
        })
    return result

ajax.LIVESEARCH_CALLBACK = solr_livesearch_callback