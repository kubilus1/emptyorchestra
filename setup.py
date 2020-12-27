#!/usr/bin/env python

#from distutils.core import setup
from setuptools import setup

setup(
    name='emptyorchestra',
    version='0.1.0',
    author='Matt Kubilus',
    author_email="kubilus1@yahoo.com",
    url="www.kubilus.com/emptyorch",
    packages=['emptyorchestra'],
    package_dir = {'emptyorchestra':'src'},
    package_data = {
        'emptyorchestra':[
            'static/css/*.css',
            'static/js/*.js',
            'static/images/*.jpeg',
            'static/tracks/*.mp3',
            'static/*.mp3',
            'templates/*.html',
            'templates/*.js',
            'eo_conf.yml'
        ]
    },
    entry_points = {
        'console_scripts': ['emptyorch=emptyorchestra.eo_web:main'],
    },
    install_requires=[
        'jinja2 < 3.0',
        'tinydb == 3.15.2',
        'Flask >= 0.12',
        'pywebview >= 3.4',
        'gTTS == 2.2.1',
        'xmltodict < 0.12',
        'pyyaml',
        'unlimited-youtube-search',
        'flask-cors'
    ]
    #scripts=['src/emptyorch']
)

