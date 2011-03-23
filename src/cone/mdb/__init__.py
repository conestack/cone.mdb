import cone.app
from cone.mdb.model.solr import Solr
from cone.mdb.model.amqp import Amqp
from cone.mdb.model.database import Database
from cone.mdb.model.repositories import Repositories

cone.app.cfg.css.protected.append('mdb-static/styles.css')
cone.app.cfg.js.protected.append('mdb-static/mdb.js')

cone.app.register_plugin_config('solr', Solr)
cone.app.register_plugin_config('amqp', Amqp)
cone.app.register_plugin_config('database', Database)

cone.app.register_plugin('repositories', Repositories)


def pub_main(global_config, **settings):
    from pyramid.config import Configurator
    from cone.mdb import public
    
    config = Configurator(settings=settings)
    config.begin()
    
    config.add_route(
        'search',
        '/search/{term}',
        view=public.search,
        #accept='application/json',
        renderer='json')
    
    config.add_route(
        'access',
        '/access/{uid}',
        view=public.access,
        #accept='application/json',
        renderer='json')
    
    config.add_route(
        'info',
        '/info/{uid}',
        view=public.info,
        #accept='application/json',
        renderer='json')
    
    config.add_route(
        'download_active',
        '/{uid}',
        view=public.download)
    
    config.add_route(
        'download_specific',
        '/{uid}/{rev}',
        view=public.download)
    
    config.end()
    return config.make_wsgi_app()
