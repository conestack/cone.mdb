import uuid
import datetime
from pyramid.security import authenticated_userid
from cone.app.model import (
    Properties,
    AdapterNode,
    BaseNodeInfo,
    registerNodeInfo,
)
from node.ext.mdb import (
    Revision as MDBRevision,
    Metadata as MDBMetadata,
    Binary as MDBBinary,
)
from cone.app.browser.utils import nodepath
from cone.mdb.model.utils import (
    solr_config,
    timestamp,
)
from cone.mdb.solr import Metadata as SolrMetadata


# valid metadata keys
solr_whitelist = [
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

solr_date_keys = [
    'created',
    'effective',
    'expires',
    'modified',
]

sorl_non_metadata_keys = [
    'path',
    'revision',
]


def set_metadata(metadata, data):
    """Set metadata on revision.
    
    ``metadata``
        node.ext.mdb.Metadata
    ``kw``
        dict containing metadata
    """
    for key, val in data.items():
        if not key in solr_whitelist:
            continue
        setattr(metadata, key, val)


def solr_date(dt):
    """Return date string acceppted by solr.
    
    ``dt``
        datetime.datetime
    """
    if isinstance(dt, datetime.datetime):
        date = '%sZ' % dt.isoformat()
        return date


def index_metadata(config, revision):
    """Index revision metadata in solr.
    
    ``config``
        cone.mdb.solr.Config
    ``revision``
        node.ext.mdb.Revision
    """
    try:
        md = dict()
        md['path'] = '/'.join(nodepath(revision))
        md['revision'] = revision.__name__
        metadata = revision['metadata']
        for key in metadata.keys():
            # value not available on metadata
            if key in sorl_non_metadata_keys:
                continue
            # non indexed metadata is ignored
            if not key in solr_whitelist:
                continue
            val = getattr(metadata, key)
            # convert value to solr accepted date format if dt instance
            if key in solr_date_keys:
                date = solr_date(val)
                if not date:
                    continue
                md[key] = date
                continue
            md[key] = val
        solr_md = SolrMetadata(config, solr_whitelist, **md)
        solr_md()
    except Exception, e:
        # logging
        print e
        # debug
        raise


def add_revision(request, media, data):
    """Add revision to media.
    
    ``request``
        webob request
    ``media``
        cone.mdb.model.Media
    ``data``
        revision data
    """
    keys = [int(key) for key in media.keys()]
    keys.sort()
    if keys:
        key = str(keys[-1] + 1)
    else:
        key = '0'
    revision = MDBRevision()
    mdb_media = media.model
    mdb_media[key] = revision
    metadata = MDBMetadata()
    revision['metadata'] = metadata
    file = data['data']
    if not file:
        payload = ''
    else:
        if isinstance(file, basestring):
            payload = file
        else:
            payload = file['file'].read()
            metadata.metatype = file['mimetype']
            metadata.filename = file['filename']
    revision['binary'] = MDBBinary(payload=payload)
    metadata.revision = key
    metadata.uid = str(uuid.uuid4())
    metadata.created = timestamp()
    metadata.creator = authenticated_userid(request)
    
    # XXX: repoze.workflow
    metadata.flag = 'draft'
    
    metadata.url = '' # calculate tiny url for frontend
    metadata.visibility = data['visibility']
    metadata.body = data['body']
    
    set_metadata(metadata, data)
    media()
    index_metadata(solr_config(media), revision)


def update_revision(request, revision, data):
    """Update revision.
    
    ``request``
        webob request
    ``media``
        cone.mdb.model.Revision
    ``data``
        revision data
    """
    metadata = revision.metadata
    file = data['data']
    if not file:
        payload = ''
    else:
        if isinstance(file, basestring):
            payload = file
        else:
            payload = file['file'].read()
            metadata.metatype = file['mimetype']
            metadata.filename = file['filename']
    revision.model['binary'].payload = payload
    if not metadata.creator:
        metadata.creator = authenticated_userid(request)
    flag = data['flag']
    
    # XXX repoze.workflow callback
    if flag == 'active' and metadata.flag == 'draft':
        media = revision.__parent__
        for key in media.keys():
            rev = media[key]
            if rev.metadata.flag == 'active':
                rev.metadata.flag = 'frozen'
                rev()
    metadata.flag = flag
    
    visibility = data['visibility']
    if flag == 'active':
        visibility = 'anonymous'
    metadata.visibility = visibility
    metadata.body = data['body']
    
    set_metadata(metadata, data)
    revision()
    index_metadata(solr_config(revision), revision.model)


class RevisionAdapter(AdapterNode):
    
    node_info_name = 'revision'
    
    @property
    def properties(self):
        props = Properties()
        props.in_navtree = True
        flag = self.metadata.flag
        props.editable = flag == 'draft' and True or False
        props.action_up = True
        props.action_view = True
        return props
    
    @property
    def metadata(self):
        if self.model:
            return self.model['metadata']
        return Properties()                                 #pragma NO COVERAGE
    
    def __iter__(self):
        return iter(list())
    
    iterkeys = __iter__
    
    def __call__(self):
        self.model()


info = BaseNodeInfo()
info.title = 'Revision'
info.description = 'A revision.'
info.node = RevisionAdapter
info.addables = []
registerNodeInfo('revision', info)