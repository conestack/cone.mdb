from cone.tile import registerTile
from cone.app.browser.layout import ProtectedContentTile
from cone.mdb.model import Repositories


registerTile('content',
             'cone.app:browser/templates/listing.pt',
             interface=Repositories,
             class_=ProtectedContentTile,
             permission='login')
