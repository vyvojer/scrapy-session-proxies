import logging

from scrapy.http import Request, Response
from scrapy.exceptions import IgnoreRequest

from .proxies import ProxyList

log = logging.getLogger(__name__)


class ProxyMiddleware:

    def __init__(self, settings):
        proxy_file = settings.get('PROXY_FILE')
        self.proxy_list = ProxyList.from_file(proxy_file)
        self.retry_times_per_proxy = settings.get('PROXY_RETRY_TIMES_PER_PROXY')
        self.retry_times_per_url = settings.get('PROXY_RETRY_TIMES_PER_URL')
        self.ban_policy = BanPolicy()

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls(crawler.settings)
        return middleware

    def process_request(self, request: Request, spider):

        proxy_item = None
        retry_times = request.meta.get('retry_times')
        proven_only = False
        if retry_times:
            if retry_times <= self.retry_times_per_url:
                log.info('Retry request to %s %s times', request.url, retry_times)
                proven_only = True
            else:
                log.info('Request to %s  retried more %s times. Request ignored', request.url, retry_times)
                raise IgnoreRequest()
        if request.meta.get('proxy'):
            proxy_item = self.proxy_list.get_proxy_by_string(request.meta.get('proxy'))
        if not proxy_item:
            log.debug("Proxy number: total=%s live=%s proven=%s", len(self.proxy_list),
                 len(self.proxy_list.live_proxies), len(self.proxy_list.proven_proxies))
            proxy_item = self.proxy_list.get_random_proxy(proven_only=proven_only)
        request.meta['proxy'] = proxy_item.to_scrapy()
        request.meta['cookiejar'] = proxy_item.cookiejar
        request.meta['download_slot'] = proxy_item.download_slot()
        request.headers.setdefault('User-Agent', proxy_item.user_agent)

    def process_response(self, request: Request, response: Response, spider):
        proxy = request.meta.get('proxy')
        if proxy:
            proxy_item = self.proxy_list.get_proxy_by_string(proxy)
        if proxy_item:
            proxy_item.is_checked = True
        if proxy_item and self.ban_policy.response_is_ban(request, response):
            proxy_item.is_checked = True
            log.info('Removing banned proxy %s, %s proxies left',
                     proxy_item, len(self.proxy_list.live_proxies))
            proxy_item.is_banned = True
            retry_times = request.meta.get('retry_times', 1)
            parent_request = request.meta.get('parent_request')
            if not parent_request:
                retry_request = request.copy()
            else:
                retry_request = parent_request.copy()
            retry_request.meta['proxy'] = None
            retry_request.meta['retry_times'] = retry_times
            retry_request.dont_filter = True
            return retry_request
        return response

    def process_exception(self, request, exception, spider):
        log.debug("Exception: %s", exception)
        proxy = request.meta.get('proxy')
        if proxy is None:
            return
        else:
            retry_times = request.meta.get('retry_times', 1)
            proxy_item = self.proxy_list.get_proxy_by_string(proxy)
            if proxy_item:
                proxy_item.is_tried = True
                proxy_item.failed_num += 1
                log.debug('Proxy %s failed %s times', proxy_item, proxy_item.failed_num)
                if proxy_item.failed_num >= self.retry_times_per_proxy:
                    proxy_item.is_dead = True
                    log.info('Removing failed proxy %s, %s proxies left',
                             proxy_item, len(self.proxy_list.live_proxies))
                if True or retry_times < self.retry_times_per_url:
                    parent_request = request.meta.get('parent_request')
                    if not parent_request:
                        retry_request = request.copy()
                    else:
                        retry_request = parent_request.copy()
                    retry_request.meta['retry_times'] = retry_times + 1
                    retry_request.meta['proxy'] = None
                    retry_request.dont_filter = True
                    return retry_request


class BanPolicy:

    NOT_BAN_STATUSES = [200]
#    NOT_BAN_STATUSES = [200, 301, 302]

    def response_is_ban(self, request, response):
        if response.status not in self.NOT_BAN_STATUSES:
            return True
        if response.status == 200 and not len(response.body):
            return True
        return False

    def exception_is_ban(self, request, exception):
        return False



