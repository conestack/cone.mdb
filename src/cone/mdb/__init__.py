import cone.app
from cone.mdb.model.solr import Solr
from cone.mdb.model.amqp import Amqp
from cone.mdb.model.database import Database

cone.app.cfg.css.protected.append('mdb-static/styles.css')

cone.app.register_plugin_config('solr', Solr)
cone.app.register_plugin_config('amqp', Amqp)
cone.app.register_plugin_config('database', Database)

#cone.app.register_plugin(key, factory)