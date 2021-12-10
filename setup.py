from setuptools import setup, find_packages

# read the contents of your README file
import io
from os import path
this_directory = path.abspath(path.dirname(__file__))
with io.open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

requirements = [
    'Click>=6.0',
    'boto3>=1.5.33',
    'reprint>=0.5.1',
    'configparser>=3.5.0'
]

setup(
    name="ecstools",
    version="0.2.6",
    url="https://github.com/boroivanov/ecs-tools",

    author='Borislav Ivanov',
    author_email='borogl@gmail.com',

    description='Utilities for AWS ECS',
    long_description=long_description,
    long_description_content_type='text/markdown',

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
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
