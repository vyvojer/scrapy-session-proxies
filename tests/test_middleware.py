import unittest
import json
import logging

log = logging.getLogger(__name__)

from scrapy import Spider
from scrapy.http import Request, Response
from scrapy.crawler import CrawlerProcess

items = []
user_agents = {}


class TestSpider(Spider):
    name = "test_spider"

    custom_settings = {
#        'LOG_FILE': "test.log",
        'CONCURRENT_REQUESTS_PER_DOMAIN': 40,
        'PROXY_FILE': 'proxies.txt',
        'PROXY_RETRY_TIMES_PER_PROXY': 5,
        'PROXY_RETRY_TIMES_PER_URL': 10,
        'RETRY_ENABLED': False,
        'DOWNLOAD_TIMEOUT': 10,
        'COOKIES_DEBUG': False,
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_session_proxies.middlewares.ProxyMiddleware': 90,
        #   'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
        }
    }

    SET_URL = 'https://httpbin.org/cookies/set/{name}/{value}'
    HEADER_URL = 'https://httpbin.org/headers'
    WRONG_URL = 'https://httpbinsdlsjdf.org/headers'

    def start_requests(self):
        yield Request(self.WRONG_URL, dont_filter=True)
        for proxy_num in range(40):
            url = self.SET_URL.format(name='1st_request', value='1')
            request = Request(url=url,
                              callback=self.parse_first_request,
                              dont_filter=True)
            request.meta['parent_request'] = request
            yield request

    @staticmethod
    def get_data(response) -> dict:
        if response.meta.get('splash'):
            # For splash request we must rewrap json
            pass
        else:
            return json.loads(response.text)

    def parse(self, response):
        pass

    def parse_first_request(self, response):
        parent_request = response.meta['parent_request']
        proxy = response.meta['proxy']
        download_slot = response.meta['download_slot']
        url = self.SET_URL.format(name='2nd_request', value=download_slot)
        request = Request(url=url,
                          callback=self.parse_second_request,
                          dont_filter=True)
        request.meta['proxy'] = proxy
        request.meta['parent_request'] = parent_request
        yield request

    def parse_second_request(self, response):
        parent_request = response.meta['parent_request']
        proxy = response.meta['proxy']
        download_slot = response.meta['download_slot']
        url = self.SET_URL.format(name='3rd_request', value=download_slot)
        request = Request(url=url,
                          callback=self.parse_third_request,
                          dont_filter=True)
        request.meta['proxy'] = proxy
        request.meta['parent_request'] = parent_request
        yield request

    def parse_third_request(self, response):
        parent_request = response.meta['parent_request']
        proxy = response.meta['proxy']
        download_slot = response.meta['download_slot']
        url = self.SET_URL.format(name='4th_request', value=download_slot)
        request = Request(url=url,
                          callback=self.parse_cookies,
                          dont_filter=True)
        request.meta['proxy'] = proxy
        request.meta['parent_request'] = parent_request
        yield request

    def parse_cookies(self, response: Response):
        parent_request = response.meta['parent_request']
        r_dict = self.get_data(response)
        cookies = r_dict['cookies']
        items.append(cookies)
        proxy = response.meta['proxy']
        download_slot = response.meta['download_slot']
        url = self.HEADER_URL
        request = Request(url=url,
                          callback=self.parse_header_first_request,
                          dont_filter=True)
        request.meta['proxy'] = proxy
        request.meta['parent_request'] = parent_request
        yield request

    def parse_header_first_request(self, response: Response):
        parent_request = response.meta['parent_request']
        r_dict = self.get_data(response)
        user_agent = r_dict['headers']['User-Agent']
        proxy = response.meta['proxy']
        download_slot = response.meta['download_slot']
        slot_agents = user_agents.setdefault(download_slot, list())
        slot_agents.append(user_agent)
        url = self.HEADER_URL
        request = Request(url=url,
                          callback=self.parse_header_second_request,
                          dont_filter=True)
        request.meta['proxy'] = proxy
        request.meta['parent_request'] = parent_request
        yield request

    def parse_header_second_request(self, response: Response):
        parent_request = response.meta['parent_request']
        r_dict = json.loads(response.text)
        user_agent = r_dict['headers']['User-Agent']
        proxy = response.meta['proxy']
        download_slot = response.meta['download_slot']
        slot_agents = user_agents.setdefault(download_slot, list())
        slot_agents.append(user_agent)
        url = self.HEADER_URL
        request = Request(url=url,
                          callback=self.parse_header_third_request,
                          dont_filter=True)
        request.meta['proxy'] = proxy
        request.meta['parent_request'] = parent_request
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
        log.debug("User items %s", items)
        for item in items:
            self.assertEqual(item['2nd_request'], item['3rd_request'])
            self.assertEqual(item['4th_request'], item['3rd_request'])

    def test_user_agent(self):
        log.debug("User agents %s", user_agents)
        all_agents = []
        for agents in user_agents.values():
            self.assertEqual(len(set(agents)), 1)
            all_agents += agents
        for agent in all_agents:
            self.assertNotIn('Scrapy', agent)
        self.assertGreater(len(set(all_agents)), 1)



