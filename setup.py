from distutils.core import setup

setup(
    name='queuelib',
    version='1.0',
    license='BSD',
    description='Collection of persistent (disk-based) queues',
    long_description=open('README.rst').read(),
    author='Scrapy project',
    author_email='info@scrapy.org',
    url='http://github.com/scrapy/queuelib',
    packages=['queuelib', 'queuelib.tests'],
    platforms = ['Any'],
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ]
)
