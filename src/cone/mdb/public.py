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


def chk_publication(md):
    now = datetime.datetime.now()
    effective = md.get('effective')
    if effective and solr2dt(effective) > now:
        return False
    expires = md.get('expires')
    if expires and solr2dt(expires) < now:
        return False
    return True


revision_info_fl = 'uid,suid,state,revision,title,description,' + \
                    'mimetype,filename,size,alttag,effective,expires'


def revision_info(md):
    return {
        'uid': md.uid,
        'suid': md.suid,
        'state': md.state,
        'revision': md.revision,
        'title': md.title,
        'description': md.description,
        'mimetype': md.mimetype,
        'filename': md.filename,
        'size': md.size,
        'alttag': md.get('alttag', ''),
        'effective': md.get('effective', ''),
        'expires': md.get('expires', ''),
    }


def download(request):
    suid = request.matchdict['suid']
    rev = request.matchdict.get('rev')
    root = get_root()
    config = solr_config(root)
    query = Term('suid', suid)
    if rev:
        query = query & Term('revision', rev)
    else:
        query = query & Term('state', 'active')
    query = query & Term('visibility', 'anonymous')
    md = Metadata(config, SOLR_FIELDS)
    fl = 'effective,expires,physical_path,mimetype,filename'
    result = md.query(q=query, fl=fl)
    if len(result) != 1:
        raise MDBError(u'Dataset not found in SOLR. Query: %s' % query)
    md = result[0]
    if not chk_publication(md):
        raise MDBError(u'Item not effective or already expired')
    physical_path = u'/xsendfile%s.binary' % md['physical_path']
    response = Response()
    response.content_type = md['mimetype']
    response.content_disposition = \
        'attachment; filename=%s' % md['filename']
    response.headers.add('X-Accel-Redirect', physical_path)
    return response


def search(request):
    root = get_root()
    config = solr_config(root)
    result = list()
    term = '%s*~' % request.matchdict['term']
    query = Term('type', 'Media') \
          & Group(Term('title', term) \
                | Term('description', term) \
                | Term('creator', term))
    fl = 'uid,title,description,repository'
    for md in Metadata(config, SOLR_FIELDS).query(q=query, fl=fl):
        suid = str(base62(int(uuid.UUID(md.uid))))
        result.append({
            'suid': suid,
            'uid': md.uid,
            'title': md.title,
            'description': md.description,
            'repository': md.repository,
            'revisions': list(),
        })
        rev_query = Term('suid', suid) & Term('visibility', 'anonymous')
        fl = revision_info_fl
        for rev_md in Metadata(config, SOLR_FIELDS).query(q=rev_query, fl=fl):
            if not chk_publication(rev_md):
                continue
            result[-1]['revisions'].append(revision_info(rev_md))
    return result


def access(request):
    root = get_root()
    config = solr_config(root)
    uid = request.matchdict['uid']
    query = Term('uid', uid) & Term('visibility', 'anonymous')
    md = Metadata(config, SOLR_FIELDS)
    fl = 'effective,expires'
    result = md.query(q=query, fl=fl)
    if len(result) != 1:
        return False
    md = result[0]
    if not chk_publication(md):
        return False
    return True


def info(request):
    root = get_root()
    config = solr_config(root)
    uid = request.matchdict['uid']
    query = Term('uid', uid) & Term('visibility', 'anonymous')
    md = Metadata(config, SOLR_FIELDS)
    result = md.query(q=query, fl=revision_info_fl)
    if len(result) != 1:
        return {}
    md = result[0]
    if not chk_publication(md):
        return {}
    return revision_info(md)