import os
import tempfile
import shutil
from plone.testing import Layer
from cone.app import root
from cone.app.testing import Security

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
        os.mkdir(os.path.join(self.tempdir, 'repo1'))
        os.mkdir(os.path.join(self.tempdir, 'repo2'))
    
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