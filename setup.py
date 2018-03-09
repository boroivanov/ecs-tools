import codecs
import os.path
import re

from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    return codecs.open(os.path.join(here, *parts), 'r').read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


requirements = [
    'Click>=6.0',
    'boto3>=1.5.33',
    'reprint>=0.5.1'
]

setup(
    name="ecstools",
    version=find_version('ecstools', '__init__.py'),
    url="https://github.com/boroivanov/ecs-tools",

    author='Borislav Ivanov',
    author_email='borogl@gmail.com',

    description='Utilities for AWS ECS',

    packages=find_packages(),
    install_requires=requirements,
    include_package_data=True,
    package_dir={'ecstools':
                 'ecstools'},
    entry_points={
        'console_scripts': [
            'ecs=ecstools.main:cli'
        ]
    },

    license="MIT license",

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
