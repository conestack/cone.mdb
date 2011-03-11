import os
import atexit
from zamqp import (
    AMQPProps,          
    AMQPEventCallback,
    AMQPConsumer,
    AMQPThread,
)
from cone.app.model import ConfigProperties
from cone.mdb.model.utils import APP_PATH

def create_consumer():
    try:
        path = os.path.join(APP_PATH, 'etc', 'amqp.cfg')
        config = ConfigProperties(path)
        props = AMQPProps(host=config.host,
                          user=config.user,
                          password=config.password,
                          ssl=config.ssl == 'True',
                          exchange=config.exchange,
                          type=config.type,
                          realm=config.realm)
        callback = AMQPEventCallback()
        consumer = AMQPThread(AMQPConsumer(config.queue, props, callback))
        consumer.start()
        return consumer
    except Exception, e:
        print 'AMQP Error: %s' % str(e)

# XXX: later
#consumer = create_consumer()
#
#def cleanup():
#    if consumer:
#        consumer.close()
#
#atexit.register(cleanup)
