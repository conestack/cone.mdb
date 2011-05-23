from setuptools import setup, find_packages
import sys, os

version = '0.9dev'
shortdesc = 'cone.mdb'
longdesc = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

setup(name='cone.mdb',
      version=version,
      description=shortdesc,
      long_description=longdesc,
      classifiers=[
            'Development Status :: 3 - Alpha',
            'Environment :: Web Environment',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
      ],
      keywords='',
      author='BlueDynamics Alliance',
      author_email='dev@bluedynamics.com',
      url=u'http://github.com/bluedynamics/cone.mdb',
      license='GNU General Public Licence',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['cone'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'cone.app',
          'pysolr',
          'repoze.workflow',
          'node.ext.mdb',
          'node.ext.ugm',
          'zamqp',
          'bda.basen',
          'hurry.filesize',
      ],
      extras_require = dict(
          test=[
                'interlude',
          ]
      ),
      tests_require=[
          'interlude',
      ],
      test_suite = "cone.ugm.tests.test_suite",
      entry_points = """\
      [paste.app_factory]
      pub_main = cone.mdb:pub_main
      """
      )
