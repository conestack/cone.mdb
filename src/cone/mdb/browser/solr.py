import os
from plumber import plumber
from pysolr import Solr as PySolr
from cone.tile import (
    Tile,
    tile,
    registerTile,
)
from cone.mdb.model import Solr
from cone.mdb.model.media import index_media
from cone.mdb.model.revision import index_revision
from cone.app.browser.layout import ProtectedContentTile
from cone.app.browser.form import (
    Form,
    YAMLForm,
)
from cone.app.browser.settings import SettingsPart
from cone.app.browser.utils import make_url
from cone.app.browser.ajax import (
    ajax_continue,
    ajax_message,
    AjaxAction,
)


registerTile('content',
             'cone.mdb:browser/templates/solr.pt',
             interface=Solr,
             class_=ProtectedContentTile,
             permission='login')


@tile('rebuild', interface=Solr, permission="manage")
class Rebuild(Tile):
    
    def render(self):
        conf = self.model.attrs
        url = 'http://%s:%s/%s/' % (conf.server, conf.port, conf.basepath)
        PySolr(url).delete(q='*:*')
        repositories = self.model.root['repositories']
        count = 0
        for repository in repositories.values():
            for media in repository.values():
                index_media(media)
                count += 1
                for revision in media.values():
                    index_revision(revision)
                    count += 1
        url = make_url(self.request, node=self.model)
        continuation = [AjaxAction(url, 'content', 'inner', '.solr')]
        ajax_continue(self.request, continuation)
        message = 'Rebuilt SOLR catalog. Catalog contains now %i items' % count
        ajax_message(self.request, message, 'info')
        return u''


@tile('editform', interface=Solr, permission="manage")
class SolrSettingsForm(Form):
    __metaclass__ = plumber
    __plumbing__ = SettingsPart, YAMLForm
    
    action_resource = u'edit'
    form_template_path = os.path.join(os.path.dirname(__file__),
                                      'forms/solr.yaml')
    
    def save(self, widget, data):
        self.model.attrs.server = data.fetch('solrform.server').extracted
        self.model.attrs.port = data.fetch('solrform.port').extracted
        self.model.attrs.basepath = data.fetch('solrform.basepath').extracted
        self.model()