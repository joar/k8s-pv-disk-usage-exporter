from setuptools import setup, find_packages

install_requires = [
    'psutil==5.2.2',
    'aiohttp==2.2.0',
    'attrs==17.2.0',
    'structlog[dev]==17.2.0',
    'pykube==0.15.0',
]

setup(
    name='disk-usage-exporter',
    version='0.1.0a0',
    packages=find_packages(),
    url='https://github.com/joar/disk-usage-exporter',
    license='BSD',
    author='Joar Wandborg',
    author_email='joar@wandborg.se',
    description='Disk usage exporter for prometheus',
    entry_points={
        'console_scripts': [
            'disk-usage-exporter = disk_usage_exporter.__main__:main'
        ]
    }
)
