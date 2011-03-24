import time
import datetime
import uuid
from bda.basen import base62
from webob import Response
from cone.app import get_root
from cone.mdb.solr import (
    Group,
    Term,
    Metadata,
    SOLR_FIELDS,
)
from cone.mdb.model.utils import solr_config


class MDBError(Exception): pass


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
    md = Metadata(config, SOLR_FIELDS)
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
    response.content_disposition = \
        'attachment; filename=%s' % result[0]['filename']
    response.headers.add('X-Accel-Redirect', physical_path)
    return response


def search(request):
    root = get_root(None)
    config = solr_config(root)
    result = list()
    term = '%s*~' % request.matchdict['term']
    query = Term('type', 'Media') \
          & Group(Term('title', term) \
                | Term('description', term) \
                | Term('creator', term))
    fl = 'uid,title,description,revision'
    for md in Metadata(config, SOLR_FIELDS).query(q=query, fl=fl):
        uid = str(base62(int(uuid.UUID(md.uid))))
        result.append({
            'uid': uid,
            'title': md.title,
            'description': md.description,
            'repository': md.repository,
            'revisions': list(),
        })
        rev_query = Term('url', uid)
        fl = 'revision,title,description,metatype,filename,size,alttag'
        for rev_md in Metadata(config, SOLR_FIELDS).query(q=rev_query, fl=fl):
            result[-1]['revisions'].append({
                'revision': rev_md.revision,
                'title': rev_md.title,
                'description': rev_md.description,
                'mimetype': rev_md.metatype,
                'filename': rev_md.filename,
                'size': rev_md.size,
                'alttag': rev_md.alttag,
            })
    return result


def access(request):
    root = get_root(None)
    return Response('access')


def info(request):
    root = get_root(None)
    return Response('info')
