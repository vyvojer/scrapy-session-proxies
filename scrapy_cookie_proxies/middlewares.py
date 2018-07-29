import logging

from scrapy.http import Request

from .proxies import ProxyList

log = logging.getLogger(__name__)


class ProxyMiddleware:

    def __init__(self, settings):
        proxy_file = settings.get('PROXY_FILE')
        self.proxy_list = ProxyList.from_file(proxy_file)

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls(crawler.settings)
        return middleware

    def process_request(self, request: Request, spider):
        proxy = None
        if request.meta.get('proxy'):
            proxy = self.proxy_list.get_proxy_by_string(request.meta.get('proxy'))
        if not proxy:
            checked_only = request.meta.get('_proxies_checked_only')
            proxy = self.proxy_list.get_random_proxy(checked_only=checked_only)
        request.meta['proxy'] = proxy.to_scrapy()
        request.meta['cookiejar'] = proxy.cookiejar
        request.meta['download_slot'] = proxy.download_slot()
        request.headers.setdefault('User-Agent', proxy.user_agent)

    def process_exception(self, request, exception, spider):
        proxy = request.meta.get('proxy')
        print(proxy, exception)
        if proxy is None:
            return
        else:
            if self.proxy_list.get_proxy_by_string(proxy):
                self.proxy_list.get_proxy_by_string(proxy).dead = True
                log.info('Removing failed proxy <%s>, %d proxies left' % (
                proxy, len(self.proxy_list.live_proxies)))
            request.meta['proxy'] = None
            return request

