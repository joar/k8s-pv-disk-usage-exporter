import warnings

from setuptools import setup, find_packages

install_requires = [
    'psutil==5.2.2',
    'aiohttp==2.2.0',
    'attrs==17.2.0',
    'structlog[dev]==17.2.0',
    'pykube==0.15.0',
]


def read_version(version_module_file='disk_usage_exporter/version.py'):
    context = {}
    with open(version_module_file) as fp:
        exec(fp.read(), context)

    return context['__version__']


def read_long_description(rst_file='README.rst'):
    try:
        with open(rst_file) as fd:
            return fd.read()
    except IOError:
        warnings.warn(f'Could not read long description from {rst_file}')


version = read_version()


setup(
    name='disk-usage-exporter',
    version=version,
    url='https://github.com/joar/disk-usage-exporter',
    description='Kubernetes PersistentVolume disk usage exporter',
    long_description=read_long_description(),
    packages=find_packages(),
    license='BSD',
    author='Joar Wandborg',
    author_email='joar@wandborg.se',
    entry_points={
        'console_scripts': [
            'disk-usage-exporter = disk_usage_exporter.__main__:main'
        ]
    }
)
