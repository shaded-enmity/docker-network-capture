#!/usr/bin/python
import setuptools
setuptools.setup(
    name = 'docker-netowrk-capture',
    version = '0.1',
    scripts = ['docker-network-capture'],
    install_requires = ['docker-py==1.9.0'],
    package_data = {
	'': ['LICENSE', 'README.md', 'VERSION']
    },
    author = 'Pavel Odvody',
    author_email = 'podvody@redhat.com',
    description = 'Thin wrapper around Docker and tcpdump to get traffic coming from/to a container',
    license = 'GNU/GPLv2',
    keywords = 'docker cli network traffic capture',
    url = 'https://github.com/shaded-enmity/docker-network-capture'
)
