import uuid
import datetime
from pyramid.security import authenticated_userid
from pyramid.threadlocal import get_current_request
from repoze.workflow import get_workflow
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

import logging
logger = logging.getLogger('mdb')

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
    'flag', # XXX: rename to state somewhen
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

# XXX: via i18n
transition_names = {
    'working_copy_2_active': 'Set active',
    'active_2_working_copy': 'Make editable',
    'active_2_frozen': 'Freeze',
    'working_copy_2_frozen': 'Freeze',
    'frozen_2_working_copy': 'Make editable',
}


def persist_state(revision, info):
    """Transition callback for repoze.workflow
    """
    if info.transition[u'to_state'] == u'active':
        media = revision.__parent__
        for val in media.values():
            if val is revision:
                continue
            if val.state == u'active':
                # XXX: try to get rid of get_current_request
                request = get_current_request()
                workflow = info.workflow
                workflow.transition(val, request, u'active_2_working_copy')
    revision()
    index_metadata(solr_config(revision), revision.model)


def set_metadata(metadata, data):
    """Set metadata on revision.
    
    ``metadata``
        node.ext.mdb.Metadata
    ``data``
        dict containing metadata
    """
    for key, val in data.items():
        if not key in solr_whitelist:
            continue
        setattr(metadata, key, val)


def set_binary(revision, data):
    """Set binary on revision.
    
    ``revision``
        node.ext.mdb.Revision
    ``data``
        dict containing revision data
    """
    metadata = revision['metadata']
    file = data['data'] # XXX: rename to file somewhen
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
                # should not happen here because mdb metadata already protect
                # XXX: clean up
                continue                                    #pragma NO COVERAGE
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
        logger.error("Error while indexing to solr: %s" % str(e))
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
    metadata.revision = key
    metadata.uid = str(uuid.uuid4())
    metadata.created = timestamp()
    metadata.creator = authenticated_userid(request)
    
    # XXX: Calculate tiny url for frontend
    metadata.url = ''
    
    set_binary(revision, data)
    set_metadata(metadata, data)
    
    revision_adapter = media[revision.__name__]
    wf_name = revision_adapter.properties.wf_name
    workflow = get_workflow(RevisionAdapter, wf_name)
    workflow.initialize(revision_adapter)
    
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
    if not metadata.creator:
        metadata.creator = authenticated_userid(request)
    set_binary(revision.model, data)
    set_metadata(metadata, data)
    revision()
    index_metadata(solr_config(revision), revision.model)


class RevisionAdapter(AdapterNode):
    
    node_info_name = 'revision'
    
    @property
    def properties(self):
        props = Properties()
        props.in_navtree = True
        flag = self.state
        props.editable = flag == u'working_copy' and True or False
        props.action_up = True
        props.action_view = True
        props.wf_state = True
        props.wf_name = u'revision'
        # XXX: check in repoze.workflow the intended way for naming
        #      transitions
        props.wf_transition_names = transition_names
        return props
    
    @property
    def metadata(self):
        if self.model:
            metadata = self.model.get('metadata')
            if metadata:
                return metadata
        return Properties()                                 #pragma NO COVERAGE
    
    def _get_state(self):
        return self.metadata.flag
    
    def _set_state(self, val):
        self.metadata.flag = val
    
    state = property(_get_state, _set_state)
    
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