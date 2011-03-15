import os
from zamqp import AMQPProps
from cone.app.model import ConfigProperties
from cone.mdb.model.utils import APP_PATH

def consumer():
    from zamqp import runner
    if runner.event_consumer \
      and runner.event_consumer.isAlive():
        return None
    path = os.path.join(APP_PATH, 'etc', 'amqp.cfg')
    config = ConfigProperties(path)
    props = AMQPProps(host=config.host,
                      user=config.user,
                      password=config.password,
                      ssl=config.ssl == 'True',
                      exchange=config.exchange,
                      type=config.type,
                      realm=config.realm)
    queue = config.queue
    return runner.create_consumer(props, queue)