import unittest
import json

from scrapy import Spider
from scrapy.http import Request, Response
from scrapy.crawler import CrawlerProcess

items = []
user_agents = {}


class TestSpider(Spider):
    name = "text"

    custom_settings = {
        'CONCURRENT_REQUESTS_PER_DOMAIN': 3,
        'PROXY_FILE': 'proxies.json',
        'RETRY_ENABLED': False,
        'DOWNLOAD_TIMEOUT': 15,
        'COOKIES_DEBUG': False,
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_cookie_proxies.middlewares.ProxyMiddleware': 90,
            #   'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
        }
    }

    SET_URL = 'https://httpbin.org/cookies/set/{name}/{value}'
    HEADER_URL = 'https://httpbin.org/headers'

    def start_requests(self):
        for proxy_num in range(10):
            url = self.SET_URL.format(name='1st_request', value='1')
            request = Request(url=url, callback=self.parse_first_request, dont_filter=True)
            yield request

    def parse(self, response):
        pass

    def parse_first_request(self, response):
        proxy = response.meta['proxy']
        download_slot = response.meta['download_slot']
        url = self.SET_URL.format(name='2nd_request', value=download_slot)
        request = Request(url=url, callback=self.parse_second_request, dont_filter=True)
        request.meta['proxy'] = proxy
        yield request

    def parse_second_request(self, response):
        proxy = response.meta['proxy']
        download_slot = response.meta['download_slot']
        url = self.SET_URL.format(name='3rd_request', value=download_slot)
        request = Request(url=url, callback=self.parse_third_request, dont_filter=True)
        request.meta['proxy'] = proxy
        yield request

    def parse_third_request(self, response):
        proxy = response.meta['proxy']
        download_slot = response.meta['download_slot']
        url = self.SET_URL.format(name='4th_request', value=download_slot)
        request = Request(url=url, callback=self.parse_cookies, dont_filter=True)
        request.meta['proxy'] = proxy
        yield request

    def parse_cookies(self, response: Response):
        r_dict = json.loads(response.text)
        cookies = r_dict['cookies']
        items.append(cookies)
        proxy = response.meta['proxy']
        download_slot = response.meta['download_slot']
        url = self.HEADER_URL
        request = Request(url=url, callback=self.parse_header_first_request, dont_filter=True)
        request.meta['proxy'] = proxy
        yield request

    def parse_header_first_request(self, response: Response):
        r_dict = json.loads(response.text)
        user_agent = r_dict['headers']['User-Agent']
        proxy = response.meta['proxy']
        download_slot = response.meta['download_slot']
        slot_agents = user_agents.setdefault(download_slot, list())
        slot_agents.append(user_agent)
        url = self.HEADER_URL
        request = Request(url=url, callback=self.parse_header_second_request, dont_filter=True)
        request.meta['proxy'] = proxy
        yield request

    def parse_header_second_request(self, response: Response):
        r_dict = json.loads(response.text)
        user_agent = r_dict['headers']['User-Agent']
        proxy = response.meta['proxy']
        download_slot = response.meta['download_slot']
        slot_agents = user_agents.setdefault(download_slot, list())
        slot_agents.append(user_agent)
        url = self.HEADER_URL
        request = Request(url=url, callback=self.parse_header_third_request, dont_filter=True)
        request.meta['proxy'] = proxy
        yield request


    def parse_header_third_request(self, response: Response):
        r_dict = json.loads(response.text)
        user_agent = r_dict['headers']['User-Agent']
        proxy = response.meta['proxy']
        download_slot = response.meta['download_slot']
        slot_agents = user_agents.setdefault(download_slot, list())
        slot_agents.append(user_agent)


class MiddlewareTest(unittest.TestCase):
    process = CrawlerProcess()
    process.crawl(TestSpider)
    process.start()

    def test_cookie(self):
        for item in items:
            self.assertEqual(item['2nd_request'], item['3rd_request'])
            self.assertEqual(item['4th_request'], item['3rd_request'])

    def test_user_agent(self):
        all_agents = []
        for agents in user_agents.values():
            self.assertEqual(len(agents), 3)
            self.assertEqual(len(set(agents)), 1)
            all_agents += agents
        self.assertGreater(len(all_agents), 1)