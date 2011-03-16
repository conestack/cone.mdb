from cone.mdb.model.solr import Solr
from cone.mdb.model.amqp import Amqp
from cone.mdb.model.database import Database
from cone.mdb.model.repositories import Repositories
from cone.mdb.model.repository import (
    RepositoryAdapter,
    add_repository,
    update_repository,
)
from cone.mdb.model.media import (
    MediaAdapter,
    add_media,
    update_media,
)
from cone.mdb import amqp

# XXX: later
#      checks if amqp consumer is alive
#      maybe in cone.app
#def get_root(environ):
#    if not amqp.consumer or not amqp.consumer.is_alive():
#        amqp.consumer = amqp.create_consumer()
#    return root