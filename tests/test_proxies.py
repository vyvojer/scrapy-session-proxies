import unittest
import json

from scrapy_session_proxies.proxies import *


class ProxyListTest(unittest.TestCase):

    def setUp(self):
        self.proxies = [
            ProxyItem('192.168.0.1', '80'),
            ProxyItem('192.168.0.2', '8080'),
            ProxyItem('192.168.0.3', '80'),
        ]
        self.proxy_list = ProxyList(self.proxies)

    def test__getitem__(self):
        self.assertEqual(self.proxies[0], self.proxy_list[0])

    def test_user_agents(self):
        self.assertGreater(len(self.proxy_list.user_agents), 5)

    def test_cookiejar(self):
        self.assertEqual(self.proxy_list[0].cookiejar, 0)
        self.assertEqual(self.proxy_list[1].cookiejar, 1)
        self.assertEqual(self.proxy_list[2].cookiejar, 2)

    def test_get_proxy(self):
        proxy_item = self.proxy_list.get_proxy(ip='192.168.0.1', port='80')
        self.assertEqual(proxy_item, self.proxies[0])

    def test_get_proxy_by_sting(self):
        proxy = 'http://192.168.0.1:80'
        proxy_item = self.proxy_list.get_proxy_by_string(proxy)
        self.assertEqual(proxy_item, self.proxies[0])

    def test_live_proxies(self):
        self.proxy_list[0].is_dead = True
        self.assertEqual(len(self.proxy_list), 3)
        self.assertEqual(len(self.proxy_list.live_proxies), 2)

    def test_proven_proxies(self):
        self.proxy_list[0].is_checked = True
        self.proxy_list[1].is_checked = True
        self.proxy_list[1].is_banned = True
        self.proxy_list[2].is_checked = True
        self.proxy_list[2].is_dead = True
        self.assertEqual(len(self.proxy_list), 3)
        self.assertEqual(len(self.proxy_list.proven_proxies), 1)

    def test_from_json(self):
        json_list = [
            {"port": "53281", "ip": "168.194.152.190"},
            {"port": "3128", "ip": "177.207.193.220"},
            {"port": "8080", "ip": "188.130.174.29"},
            {"port": "53281", "ip": "191.242.212.147"}
        ]
        json_proxies = json.dumps(json_list)
        proxy_list = ProxyList.from_json(json_proxies)
        self.assertEqual(proxy_list[0], ProxyItem("168.194.152.190", "53281"))

    def test_from_json_file(self):
        proxy_list = ProxyList.from_json_file('test_from_json.json')
        self.assertEqual(proxy_list[0], ProxyItem("168.194.152.190", "53281"))

    def test_from_txt_file(self):
        proxy_list = ProxyList.from_txt_file('test_from_txt.txt')
        self.assertEqual(proxy_list[0], ProxyItem("168.194.152.190", "53281"))
        self.assertEqual(proxy_list[3], ProxyItem("191.242.212.147", "3128"))

    def test_from_file(self):
        proxy_list = ProxyList.from_file('test_from_txt.txt')
        self.assertEqual(proxy_list[0], ProxyItem("168.194.152.190", "53281"))
        self.assertEqual(proxy_list[3], ProxyItem("191.242.212.147", "3128"))
        proxy_list = ProxyList.from_file('test_from_json.json')
        self.assertEqual(proxy_list[0], ProxyItem("168.194.152.190", "53281"))
        self.assertEqual(proxy_list[3], ProxyItem("191.242.212.147", "3128"))

    def test_get_random_proxy(self):
        self.proxy_list[0].is_checked = True
        self.proxy_list[1].is_checked = True
        self.proxy_list[1].is_banned = True
        self.proxy_list[2].is_checked = True
        self.proxy_list[2].is_dead = True
        for _ in range(500):
            self.assertEqual(self.proxy_list.get_random_proxy(), self.proxy_list[0])
            self.assertEqual(self.proxy_list.get_random_proxy(proven_only=True), self.proxy_list[0])

        self.proxy_list[0].is_checked = False
        self.proxy_list[1].is_checked = True
        self.proxy_list[1].is_banned = True
        self.proxy_list[2].is_checked = True
        self.proxy_list[2].is_dead = True
        for _ in range(500):
            self.assertEqual(self.proxy_list.get_random_proxy(), self.proxy_list[0])
            self.assertEqual(self.proxy_list.get_random_proxy(proven_only=True), self.proxy_list[0])

        self.proxy_list[0].is_checked = False
        self.proxy_list[0].is_banned = False
        self.proxy_list[0].is_checked = False
        self.proxy_list[1].is_checked = True
        self.proxy_list[1].is_banned = False
        self.proxy_list[1].is_banned = False
        self.proxy_list[2].is_checked = True
        self.proxy_list[2].is_dead = True
        self.proxy_list[2].is_banned = False
        live_proxy = []
        proven_proxy = []
        for _ in range(1500):
            self.assertIn(self.proxy_list.get_random_proxy(), self.proxy_list.live_proxies)
            self.assertIn(self.proxy_list.get_random_proxy(proven_only=True), self.proxy_list.proven_proxies)
