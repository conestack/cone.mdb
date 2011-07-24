import doctest
import interlude
import pprint
import unittest2 as unittest
from plone.testing import layered
from cone.mdb import testing

optionflags = doctest.NORMALIZE_WHITESPACE | \
              doctest.ELLIPSIS | \
              doctest.REPORT_ONLY_FIRST_FAILURE

layer = testing.MDBLayer()

TESTFILES = [
    'public.txt',
##    'amqp.txt',
    'solr.txt', # XXX: this test resets solr index!!!
##    'model/amqp.txt',
    'model/database.txt',
    'model/solr.txt',
    'model/repositories.txt',
    'model/repository.txt',
    'model/media.txt',
    'model/revision.txt',
    'model/utils.txt',
##    'browser/amqp.txt',
    'browser/database.txt',
    'browser/solr.txt',
    'browser/livesearch.txt',
    'browser/repositories.txt',
    'browser/repository.txt',
    'browser/media.txt',
    'browser/revision.txt',
]

def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
        layered(
            doctest.DocFileSuite(
                testfile,
                globs={'interact': interlude.interact,
                       'pprint': pprint.pprint,
                       'pp': pprint.pprint,
                       },
                optionflags=optionflags,
                ),
            layer=layer,
            )
        for testfile in TESTFILES
        ])
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')                 #pragma NO COVERAGE