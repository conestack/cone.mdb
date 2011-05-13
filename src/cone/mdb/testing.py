import tempfile
import shutil
import datetime
import pyramid_zcml
from plone.testing import Layer
from cone.app import root
from cone.app.testing import security
from cone.mdb.model import (
    add_repository,
    add_media,
    add_revision,
)


class Database(Layer):
    """Test layer providing dummy repositories
    """
    
    defaultBases = (security,)
    
    def _add_repositories(self):
        request = self.current_request
        repositories = root['repositories']
        for i in range(1, 3):
            add_repository(
                request,
                repositories,
                'repo%i' % i,
                'Repository %i' % i,
                'Repository %i description' % i)
    
    def _add_media(self):
        request = self.current_request
        repository = root['repositories']['repo1']
        for i in range(1, 3):
            add_media(
                request,
                repository,
                'Media %i' % i,
                'Media %i description' % i)
    
    def _add_revisions(self):
        request = self.current_request
        media = root['repositories']['repo1']['a']
        for i in range(2):
            data = {
                'title': 'Revision %i' % i,
                'author': 'max%i' % i,
                'description': 'description%i' % i,
                'keywords': ['keyword_a_%i' % i, 'keyword_b_%i' % i],
                'relations': [],
                'effective': datetime.datetime(2011, 3, 1),
                'expires': datetime.datetime(2011, 3, 31),
                'alttag': 'alttag %i' % i,
                'data': 'Contents from Textfile %i' % i,
                'visibility': 'hidden',
            }
            add_revision(request, media, data)
    
    def setUp(self, args=None):
        print "Rebase MDB database root to temp directory"
        pyramid_zcml.zcml_configure('configure.zcml', 'cone.mdb')
        self.tempdir = tempfile.mkdtemp()
        self.db = root['settings']['database']
        self.orgin_db_path = self.db.attrs.path
        self.db.attrs.path = self.tempdir
        self.db()
        self.new_request()
        self.login('manager')
        self._add_repositories()
        self._add_media()
        self._add_revisions()
        self.logout()
    
    def tearDown(self):
        print "Reset to original MDB database path"
        self.db.attrs.path = self.orgin_db_path
        self.db()
        shutil.rmtree(self.tempdir)
    
    def rebase(self, path):
        self.db.attrs.path = path
        self.db()
        
    def recover(self):
        self.db.attrs.path = self.tempdir
        self.db()
    
    # XXX: better way of providing stuff from base layer below
    
    @property
    def security(self):
        return security
    
    def login(self, login):
        security.login(login)
    
    def logout(self):
        security.logout()
    
    def new_request(self):
        return security.new_request()
    
    @property
    def current_request(self):
        return security.current_request