import os
import uuid
from bda.basen import base62
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
from cone.mdb.solr import (
    index_doc,
    SOLR_FIELDS,
)

import logging
logger = logging.getLogger('mdb')


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
        revision.metadata.visibility = 'anonymous'
        media = revision.__parent__
        for val in media.values():
            if val is revision:
                continue
            if val.state == u'active':
                # XXX: try to get rid of get_current_request
                request = get_current_request()
                workflow = info.workflow
                workflow.transition(val, request, u'active_2_working_copy')
    revision.metadata.flag = info.transition[u'to_state']
    revision()
    
    path = '/'.join(nodepath(revision))
    physical_path = '/'.join(nodepath(revision.model))
    try:
        size = os.path.getsize(physical_path)
    except OSError, e:
        size = 0
    index_doc(solr_config(revision),
              revision,
              revision=revision.model.__name__,
              path=path,
              physical_path=physical_path,
              size=size)


def set_metadata(metadata, data):
    """Set metadata on revision.
    
    ``metadata``
        node.ext.mdb.Metadata
    ``data``
        dict containing metadata
    """
    for key, val in data.items():
        if not key in SOLR_FIELDS:
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
    metadata.url = str(base62(int(uuid.UUID(media.metadata.uid))))
    metadata.created = timestamp()
    metadata.creator = authenticated_userid(request)
    
    set_binary(revision, data)
    set_metadata(metadata, data)
    
    revision_adapter = media[revision.__name__]
    wf_name = revision_adapter.properties.wf_name
    workflow = get_workflow(RevisionAdapter, wf_name)
    workflow.initialize(revision_adapter)
    
    media()
    
    physical_path = '/'.join(nodepath(revision))
    try:
        size = os.path.getsize(physical_path)
    except OSError, e:
        size = 0
    index_doc(solr_config(media),
              revision_adapter,
              revision=revision.__name__,
              path='/'.join(nodepath(media) + [revision.__name__]),
              physical_path=physical_path,
              size=size)


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
    
    physical_path = '/'.join(nodepath(revision.model))
    try:
        size = os.path.getsize(physical_path)
    except OSError, e:
        size = 0
    index_doc(solr_config(revision),
              revision,
              revision=revision.model.__name__,
              path='/'.join(nodepath(revision)),
              physical_path=physical_path,
              size=size)


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