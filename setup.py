# encoding: utf-8
"""
PyApollo - Python Client for Ctrip's Apollo
================

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Easy python client to use [Apollo](https://github.com/ctripcorp/apollo)。
Tested with python 3.7

Installation
------------
- 启动客户端长连接监听

``` python
from bp_apollo_client.apollo_client import ApolloClient, ApolloData
client = ApolloClient(app_id=<appId>, cluster=<clusterName>, config_server_url=<configServerUrl>)
client.client.add_callback_funcs(<cb_funs>)  # add callback fun for get apollo push config when changed
client.start()


```

- get apollo config data
  ```
  client.get_value(Key, DefaultValue)
  # or
  ApolloData.get(Key, DefaultValue)
  ```
"""
from setuptools import setup, find_packages
import bp_apollo_client

SHORT = u'bp-apollo-client'

setup(
    name='bp-apollo-client',
    version=bp_apollo_client.__version__,
    packages=find_packages(),
    url='https://github.com/foxliu/pyapollo.git',
    author=bp_apollo_client.__author__,
    author_email='foxliu2012@gmail.com',
    classifiers=[
        'Programming Language :: Python :: 3.7',
    ],
    include_package_data=True,
    package_data={'': ['*.py', '*.pyc']},
    zip_safe=False,
    platforms='any',
    python_requires='>=3.7',

    description=SHORT,
    long_description=__doc__,
    long_description_content_type='text/markdown'
)
