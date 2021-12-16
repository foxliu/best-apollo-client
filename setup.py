# encoding: utf-8
"""
#### Apollo client python
- 启动客户端长连接监听

``` python
client = ApolloClient(app_id=<appId>, cluster=<clusterName>, config_server_url=<configServerUrl>)
client.client.add_callback_funcs(<cb_funs>)  # 添加回调函数，回调函数接收一个参数为当前appId的配置
client.start()
```

- 获取Apollo的配置
  ```
  client.get_value(Key, DefaultValue)
  ```
"""
from setuptools import setup, find_packages
import pyapollo

SHORT = u'best-apollo-client'

setup(
    name='best-apollo-client',
    version=pyapollo.__version__,
    packages=find_packages(),
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
    python_requires='>=3.7',

    description=SHORT,
    long_description=__doc__,
    long_description_content_type='text/markdown'
)
