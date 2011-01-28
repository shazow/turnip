from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(name='turnip',
    version=version,
    description="Task scheduler. Tastier than celery.",
    long_description="""\
""",
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Andrey Petrov',
    author_email='andrey.petrov@shazow.net',
    url='http://github.com/shazow/turnip',
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
        'SQLAlchemy',
        'python-dateutil',
        'croniter',
    ],
    entry_points="""
    # -*- Entry points: -*-
    """,
    scripts=['bin/turnip'],
)
