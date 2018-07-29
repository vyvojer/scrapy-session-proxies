from setuptools import setup

setup(name='scrapy-cookie-proxies',
      version='0.0.2',
      description='Scrapy proxy, cookie, user_agent middleware',
      url='http://bitbucket.org/storborg/funniest',
      author='Alexey Londkevich',
      author_email='vyvojer@gmail.com',
      license='MIT',
      packages=['scrapy_cookie_proxies'],
      package_data={
            'scrapy_cookie_proxies': ['mobile_agents.txt',]
      },
      install_requires=['scrapy'],
      zip_safe=False)
