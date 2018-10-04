from setuptools import setup

setup(name='scrapy-session-proxies',
      version='0.0.2',
      description='Scrapy proxy middleware with session support',
      url='http://bitbucket.org/storborg/funniest',
      author='Alexey Londkevich',
      author_email='vyvojer@gmail.com',
      license='MIT',
      packages=['scrapy_session_proxies'],
      package_data={
          'scrapy_session_proxies': ['mobile_agents.txt', ]
      },
      install_requires=['scrapy'],
      zip_safe=False)
