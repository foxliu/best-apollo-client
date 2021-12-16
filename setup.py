# encoding: utf-8
"""
pyapollo 常用工具包


"""
from setuptools import setup, find_packages
import pyapollo

SHORT = u'pyapollo'

setup(
    name='pyapollo',
    version=pyapollo.__version__,
    packages=find_packages(),
    install_requires=[
        'requests',
        'pyyaml'
    ],
    url='https://github.com/foxliu/pyapollo.git',
    author=pyapollo.__author__,
    author_email='foxliu2012@gmail.com',
    classifiers=[
        'Programming Language :: Python :: 3.7',
    ],
    include_package_data=True,
    package_data={'': ['*.py', '*.pyc']},
    zip_safe=False,
    platforms='any',

    description=SHORT,
    long_description=__doc__,
)
