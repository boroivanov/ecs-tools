from setuptools import setup, find_packages


requirements = [
    'Click>=6.0',
    'boto3>=1.5.33',
    'reprint>=0.5.1',
    'configparser>=3.5.0'
]

setup(
    name="ecstools",
    version="0.1.6",
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
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
