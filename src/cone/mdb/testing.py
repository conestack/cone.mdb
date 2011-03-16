import os
import tempfile
import shutil
from plone.testing import Layer
from pyramid.testing import DummyRequest
from cone.app import root
from cone.app.testing import Security
from cone.mdb.model import add_repository

security = Security()

class Database(Layer):
    """Test layer providing dummy repositories
    """
    
    defaultBases = (security,)
    
    def setUp(self, args=None):
        print "Rebase MDB database root to temp directory"
        self.tempdir = tempfile.mkdtemp()
        self.db = root['settings']['database']
        self.orgin_db_path = self.db.attrs.path
        self.db.attrs.path = self.tempdir
        self.db()
        request = DummyRequest()
        self.authenticate('manager')
        repositories = root['repositories']
        for i in range(1, 3):
            add_repository(request,
                           repositories,
                           'repo%i' % i,
                           'Repository %i' % i,
                           'Repository %i description' % i)
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
    
    def authenticate(self, login):
        security.authenticate(login)
    
    def logout(self):
        security.logout()