"""Setup configuration for tradingview-scraper package."""

from setuptools import setup, find_packages

def readme():
    """Read README.md file."""
    with open('README.md', encoding='utf-8') as f:
        readme_content = f.read()
    return readme_content

classifiers = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'Intended Audience :: Financial and Insurance Industry',
    'Operating System :: OS Independent',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.11',
    'Programming Language :: Python :: 3.12',
    'Programming Language :: Python :: 3.13',
    'Topic :: Office/Business :: Financial :: Investment',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

VERSION = '0.4.21'
DESCRIPTION = 'A powerful Python library for scraping real-time market data, indicators, and ideas from TradingView.'

setup(
    name="tradingview-scraper",
    version=VERSION,
    author="Smit Kunpara",
    author_email="smitkunpara@gmail.com",
    url='https://github.com/smitkunpara/tradingview-scraper',
    download_url=f'https://github.com/smitkunpara/tradingview-scraper/archive/refs/tags/v{VERSION}.zip',
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=readme(),
    license='MIT',
    packages=find_packages(),
    package_data={
        'tradingview_scraper': [
            'data/areas.json',
            'data/exchanges.txt',
            'data/indicators.txt',
            'data/languages.json',
            'data/news_providers.txt',
            'data/timeframes.json',
        ],
    },
    python_requires='>=3.11',
    install_requires=[
        "setuptools",
        "requests>=2.32.4",
        "pandas>=2.0.3",
        "beautifulsoup4>=4.12.3",
        "pydantic>=2.8.2",
        "websockets>=13.1",
        "websocket-client>=1.8.0",
        "python-dotenv>=1.0.1",
    ],
    keywords=['tradingview', 'scraper', 'python', 'finance', 'market-data', 'technical-analysis', 'real-time'],
    classifiers=classifiers
)