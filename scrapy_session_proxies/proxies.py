import re
import random
import json
import os, os.path
from typing import Iterable


class ProxyItem:
    def __init__(self, ip, port, user_agent=None, cookiejar: int=None):
        self.ip = ip
        self.port = port
        self.user_agent = user_agent
        self.cookiejar = cookiejar
        self.is_checked = False
        self.is_dead = False
        self.is_banned = False
        self.failed_num = 0

    def __repr__(self):
        cls_repr = self.__class__.__name__
        repr = "{}(ip={}, port={}, user_agent={}, cookiejar={})"
        return repr.format(cls_repr, self.ip, self.port, self.user_agent, self.cookiejar)

    def __str__(self):
        return "{}:{}".format(self.ip, self.port)

    def __eq__(self, other):
        return (self.ip, self.port) == (other.ip, other.port)

    def to_scrapy(self):
        return 'http://{}:{}'.format(self.ip, self.port)

    def download_slot(self):
        return "{}-{}".format(self.ip.replace(".", "_"), self.port)


class ProxyList:

    def __init__(self, proxies: Iterable[ProxyItem]):
        self.proxies = list(proxies)
        module_dir = os.path.dirname(os.path.realpath(__file__))
        ua_path = os.path.join(module_dir, 'mobile_agents.txt')
        self.user_agents = self._load_user_agents(ua_path)
        for index, proxy in enumerate(self.proxies):
            proxy.cookiejar = index
            proxy.user_agent = random.choice(self.user_agents)

    def __getitem__(self, item):
        return self.proxies[item]

    def __len__(self):
        return len(self.proxies)

    @staticmethod
    def _load_user_agents(path):
        with open(path) as file:
            user_agents = [line.rstrip('\n') for line in file]
        return user_agents

    @property
    def live_proxies(self):
        return [proxy for proxy in self.proxies if not proxy.is_dead and not proxy.is_banned]

    @property
    def proven_proxies(self):
        return [proxy for proxy in self.proxies if proxy.is_checked and not proxy.is_dead and not proxy.is_banned]

    def get_proxy(self, ip: str, port: str) -> ProxyItem:
        matches = [proxy for proxy in self.proxies if proxy.ip == ip and proxy.port == port]
        if matches:
            return matches[0]

    def get_proxy_by_string(self, proxy:str) -> ProxyItem:
        pattern = re.compile('//(.+?):(\d+)')
        match = pattern.search(proxy)
        if match:
            ip = match.group(1)
            port = match.group(2)
            return self.get_proxy(ip, port)

    def get_random_proxy(self, proven_only=False):
        if proven_only and self.proven_proxies:
            return random.choice(self.proven_proxies)
        else:
            return random.choice(self.live_proxies)

    @classmethod
    def from_json(cls, proxies: json):
        proxies = [ProxyItem(proxy['ip'], proxy['port']) for proxy in json.loads(proxies)]
        return cls(proxies)

    @classmethod
    def from_json_file(cls, path):
        with open(path) as file:
            proxies = [ProxyItem(proxy['ip'], proxy['port']) for proxy in json.load(file)]
        return cls(proxies)

    @classmethod
    def from_file(cls, path):
        _, extension = os.path.splitext(path)
        if extension == '.txt':
            return ProxyList.from_txt_file(path)
        if extension == '.json':
            return ProxyList.from_json_file(path)

    @classmethod
    def from_txt_file(cls, path):
        proxies = []
        with open(path) as file:
            for line in file:
                match = re.search('(\d+\.\d+\.\d+\.\d+):(\d+)', line)
                if match:
                    ip = match.group(1)
                    port = match.group(2)
                    proxies.append(ProxyItem(ip, port))
        return cls(proxies)

