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
        'tinydb >= 3.7',
        'Flask >= 0.12',
        'pywebview',
        'gTTS',
        'xmltodict',
        'pyyaml'
    ]
    #scripts=['src/emptyorch']
)
