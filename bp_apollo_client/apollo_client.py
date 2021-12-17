#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import os.path
import threading
import time
import yaml

import requests


class GlobalVar:
    """Global Vars"""
    name = 'best_apollo_client'

    def set(self, name, value):
        setattr(self, name, value)

    def get(self, name, default_value=None):
        return getattr(self, name, default_value)


ApolloData = GlobalVar()


def init_config(apollo_data: dict):
    """初始化配置信息"""
    logging.getLogger(__name__).debug(f'get apollo data: {apollo_data}')
    for k, v in apollo_data.items():
        ApolloData.set(k, v)


class ApolloClient(object):
    """Get config from Apollo"""

    def __init__(self, app_id, cluster='default', config_server_url='http://localhost:8080', timeout=10, ip=None,
                 log_config=False, log_store_path='/tmp/apollo_config/'):
        """
        :param app_id: Apollo config AppId
        :param cluster: Apollo config Cluster
        :param config_server_url: Apollo Meta Server URL
        :param timeout: Client notifications Apollo Meta Server timeout
        :param ip: Default local ip
        :param log_config: bool For Debug, Is store App config to local file
        :param log_store_path: Dir for store config file, the file name is apollo release key
        """
        self.config_server_url = config_server_url
        self.appId = app_id
        self.cluster = cluster
        self.timeout = timeout
        self.log_config = log_config
        self.log_store_path = log_store_path
        self.stopped = False
        self.ip = None
        self.init_ip(ip)
        self.callback_funcs = [init_config]

        self._stopping = False
        self._cache = {}
        self._notification_map = {'application': -1}

    def init_ip(self, ip):
        if ip:
            self.ip = ip
        else:
            import socket
            s = None
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(('8.8.8.8', 53))
                ip = s.getsockname()[0]
            finally:
                if s:
                    s.close()
            self.ip = ip

    # Main method
    def get_value(self, key, default_val=None, namespace='application', auto_fetch_on_cache_miss=False):
        if namespace not in self._notification_map:
            self._notification_map[namespace] = -1
            logging.getLogger(__name__).info("Add namespace '%s' to local notification map", namespace)

        if namespace not in self._cache:
            self._cache[namespace] = {}
            logging.getLogger(__name__).info("Add namespace '%s' to local cache", namespace)
            # This is a new namespace, need to do a blocking fetch to populate the local cache
            self._long_poll()

        if key in self._cache[namespace]:
            return self._cache[namespace][key]
        else:
            if auto_fetch_on_cache_miss:
                return self._cached_http_get(key, default_val, namespace)
            else:
                return default_val

    def add_callback_funcs(self, callback_fun_list):
        if not isinstance(callback_fun_list, (list, tuple)):
            callback_fun_list = [callback_fun_list]
        self.callback_funcs.extend(callback_fun_list)

    # Start the long polling loop. Two modes are provided:
    # thread mode (default), create a worker thread to do the loop. Call self.stop() to quit the loop
    def start(self, catch_signals=True):
        # First do a blocking long poll to populate the local cache, otherwise we may get racing problems
        if len(self._cache) == 0:
            self._long_poll()
        if catch_signals:
            import signal
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGABRT, self._signal_handler)
        t = threading.Thread(target=self._listener, daemon=True)
        t.start()

    def stop(self):
        self._stopping = True
        logging.getLogger(__name__).info("Stopping listener...")

    def _cached_http_get(self, key, default_val, namespace='application'):
        url = f'{self.config_server_url}/configfiles/json/{self.appId}/{self.cluster}/{namespace}?ip={self.ip}'
        r = requests.get(url)
        if r.ok:
            data = r.json()
            self._cache[namespace] = data
            logging.getLogger(__name__).info('Updated local cache for namespace %s', namespace)
        else:
            data = self._cache[namespace]

        if self.log_config:
            self.write_config_to_file(self._cache, 'cached_config')

        if key in data:
            return data[key]
        else:
            return default_val

    def _uncached_http_get(self, namespace='application'):
        url = f'{self.config_server_url}/configs/{self.appId}/{self.cluster}/{namespace}?ip={self.ip}'
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            self._cache[namespace] = data['configurations']
            release_key = data['releaseKey']
            logging.getLogger(__name__).info('Updated local cache for namespace %s release key %s: %s',
                                             namespace, data['releaseKey'],
                                             repr(self._cache[namespace]))
            if self.log_config:
                self.write_config_to_file(self._cache, release_key)
            if self.callback_funcs:
                for fun in self.callback_funcs:
                    if callable(fun):
                        fun(self._cache[namespace])

    def _signal_handler(self, signal, frame):
        logging.getLogger(__name__).info('You pressed Ctrl+C!')
        self._stopping = True

    def _long_poll(self):
        url = f'{self.config_server_url}/notifications/v2'
        notifications = []
        for k in self._notification_map:
            notification_id = self._notification_map[k]
            notifications.append({
                'namespaceName': k,
                'notificationId': notification_id
            })

        while True:
            try:
                r = requests.get(url=url, params={
                    'appId': self.appId,
                    'cluster': self.cluster,
                    'notifications': json.dumps(notifications, ensure_ascii=False)
                }, timeout=(self.timeout, self.timeout))

                logging.getLogger(__name__).debug('Long polling returns %d: url=%s', r.status_code, r.request.url)

                if r.status_code == 304:
                    # no change, loop
                    logging.getLogger(__name__).debug('No change, loop...')
                    return

                if r.status_code == 200:
                    data = r.json()
                    for entry in data:
                        ns = entry['namespaceName']
                        nid = entry['notificationId']
                        logging.getLogger(__name__).info("%s has changes: notificationId=%d", ns, nid)
                        self._uncached_http_get(ns)
                        self._notification_map[ns] = nid
                    break
                else:
                    logging.getLogger(__name__).warning('Sleep...')
                    if not self._stopping:
                        time.sleep(self.timeout)
                    break
            except requests.Timeout:
                if not self._stopping:
                    time.sleep(self.timeout)
                else:
                    return

    def _listener(self):
        logging.getLogger(__name__).info('Entering listener loop...')
        while not self._stopping:
            self._long_poll()

        logging.getLogger(__name__).info("Listener stopped!")
        self.stopped = True

    def write_config_to_file(self, content, release_key):
        """把内容写入到本地文件中方便进行debug调试"""
        if not os.path.isdir(self.log_store_path):
            os.mkdir(self.log_store_path)
        file_path = os.path.join(self.log_store_path, release_key)
        with open(file_path, 'w') as f:
            if isinstance(content, dict):
                yaml.dump(content, f)
            else:
                f.write(content)


if __name__ == '__main__':
    pass
