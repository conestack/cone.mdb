import datetime
from cone.mdb.solr import Config

def timestamp():
    return datetime.datetime.now()

def solr_config(model):
    settings = model.root['settings']['solr']
    config = Config()
    config.server = settings.attrs.server
    config.port = settings.attrs.port
    config.path = settings.attrs.basepath
    return config