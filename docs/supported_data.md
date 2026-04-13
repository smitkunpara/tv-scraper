# Validation & Supported Values

Use this page when a method asks for a specific exchange, timeframe, language, or filter value. The sections below are meant to be the lookup surface for the valid values documented across the scraper pages.

## Jump To

- [Exchanges](#exchanges)
- [Technical indicators](#technical-indicators)
- [Timeframes](#timeframes)
- [Languages](#languages)
- [News areas](#news-areas)
- [News countries](#news-countries)
- [News providers](#news-providers)
- [News sectors](#news-sectors)
- [News corporate activities](#news-corporate-activities)
- [News economic categories](#news-economic-categories)
- [News asset markets](#news-asset-markets)

## Exchanges

These are the documented exchange values used by symbol-based methods such as `get_technicals()`, `get_fundamentals()`, `get_news_headlines()`, and most streaming calls.

```text
ADX ALOR AMEX ASX ATHEX BAHRAIN BASESWAP BCBA BCS BELEX
BER BET BINANCE BINANCEUS BINGX BIST BISWAP BITAZZA BITBNS BITCOKE
BITFINEX BITFLYER BITGET BITHUMB BITKUB BITMART BITMEX BITPANDAPRO
BITRUE BITSTAMP BITTREX BITVAVO BIVA BLACKBULL BLOFIN BME BMFBOVESPA BMV BSE BSSE
BTSE BVB BVC BVCV BVL BVMT BX BYBIT CAMELOT CAMELOT3ARBITRUM
CAPITALCOM CBOE CBOT CBOT_MINI CEXIO CFFEX CITYINDEX CME CME_MINI COINBASE
COINEX COMEX COMEX_MINI CRYPTO CRYPTOCAP CRYPTOCOM CRYPTO_SCAN CSE CSECY CSELK CSEMA
CURRENCYCOM CURVE DELTA DERIBIT DFM DJ DSEBD DUS DYDX EASYMARKETS
ECONOMICS EGX EIGHTCAP EUREX EURONEXT EUROTLX EXMO FINRA FOREXCOM FSE
FTSEMYX FTX FWB FX FXCM FXOPEN FX_IDC GATEIO GEMINI GETTEX
GLOBALPRIME GPW HAM HAN HITBTC HKEX HNX HONEYSWAP HONEYSWAPPOLYGON
HOSE HSI HTX HUOBI ICEAD ICEEUR ICESG ICEUS IDX INDEX
JSE KATANA KRAKEN KRX KSE KUCOIN LS LSE LSIN LSX
LUXSE MATBAROFEX MCX MERCADO MEXC MGEX MIL MMFINANCE MOEX MUN MYX
NAG NASDAQ NASDAQDUBAI NCDEX NEO NEWCONNECT NGM NSE
NSEKE NSENG NYMEX NYMEX_MINI NYSE NZX OANDA OKCOIN OKX OMXCOP
OMXHEX OMXICE OMXRSE OMXSTO OMXTSE OMXVSE ORCA OSE OSL OTC
PANCAKESWAP PANCAKESWAP3BSC PANCAKESWAP3ETH PANGOLIN PEPPERSTONE PHEMEX PHILLIPNOVA PIONEX POLONIEX PSE
PSECZ PSX PULSEX QSE QUICKSWAP QUICKSWAP3POLYGON QUICKSWAP3POLYGONZKEVM RAYDIUM RUS SAPSE
SAXO SET SGX SHFE SIX SKILLING SP SPARKS SPOOKYSWAP SSE
SUSHISWAP SUSHISWAPPOLYGON SWB SZSE TADAWUL TAIFEX TASE TFEX TFX THRUSTER3
TIMEX TOCOM TOKENIZE TPEX TRADEGATE TRADERJOE TRADESTATION TSE TSX TSXV
TVC TWSE UNISWAP UNISWAP3ARBITRUM UNISWAP3AVALANCHE UNISWAP3BASE UNISWAP3BSC UNISWAP3ETH UNISWAP3OPTIMISM
UNISWAP3POLYGON UPBIT UPCOM VANTAGE VELODROME VERSEETH VIE VVSFINANCE WAGYUSWAP WHITEBIT WOONETWORK XETR XEXCHANGE ZOOMEX
```

## Technical Indicators

These values are used by `Technicals.get_technicals(..., technical_indicators=[...])`.

### Momentum & Oscillators

| Indicator | Description |
|-----------|-------------|
| RSI | Relative Strength Index |
| RSI[1] | Previous RSI value |
| Stoch.K | Stochastic %K |
| Stoch.D | Stochastic %D |
| Stoch.K[1] | Previous Stochastic %K |
| Stoch.D[1] | Previous Stochastic %D |
| CCI20 | Commodity Channel Index (20) |
| CCI20[1] | Previous CCI20 value |
| ADX | Average Directional Index |
| ADX+DI | Positive directional indicator |
| ADX-DI | Negative directional indicator |
| ADX+DI[1] | Previous ADX+DI value |
| ADX-DI[1] | Previous ADX-DI value |
| AO | Awesome Oscillator |
| AO[1] | Previous Awesome Oscillator |
| AO[2] | Two periods back Awesome Oscillator |
| Mom | Momentum |
| Mom[1] | Previous momentum |
| Rec.Stoch.RSI | Stochastic RSI recommendation |
| Stoch.RSI.K | Stochastic RSI %K |
| Rec.WR | Williams %R recommendation |
| W.R | Williams %R |
| Rec.BBPower | Bollinger Bands Power recommendation |
| BBPower | Bollinger Bands Power |
| Rec.UO | Ultimate Oscillator recommendation |
| UO | Ultimate Oscillator |

### Trend, Price & Averages

| Indicator | Description |
|-----------|-------------|
| EMA10 | Exponential moving average (10) |
| EMA20 | Exponential moving average (20) |
| EMA30 | Exponential moving average (30) |
| EMA50 | Exponential moving average (50) |
| EMA100 | Exponential moving average (100) |
| EMA200 | Exponential moving average (200) |
| SMA10 | Simple moving average (10) |
| SMA20 | Simple moving average (20) |
| SMA30 | Simple moving average (30) |
| SMA50 | Simple moving average (50) |
| SMA100 | Simple moving average (100) |
| SMA200 | Simple moving average (200) |
| Rec.Ichimoku | Ichimoku recommendation |
| Ichimoku.BLine | Ichimoku baseline |
| Rec.VWMA | VWMA recommendation |
| VWMA | Volume weighted moving average |
| Rec.HullMA9 | Hull MA9 recommendation |
| HullMA9 | Hull moving average (9) |
| close | Close price |

### Recommendations & MACD

| Indicator | Description |
|-----------|-------------|
| Recommend.Other | Other recommendation score |
| Recommend.All | Overall recommendation score |
| Recommend.MA | Moving-average recommendation score |
| MACD.macd | MACD line |
| MACD.signal | MACD signal line |

### Pivot Points

| Indicator | Description |
|-----------|-------------|
| Pivot.M.Classic.S3 | Classic pivot S3 |
| Pivot.M.Classic.S2 | Classic pivot S2 |
| Pivot.M.Classic.S1 | Classic pivot S1 |
| Pivot.M.Classic.Middle | Classic pivot middle |
| Pivot.M.Classic.R1 | Classic pivot R1 |
| Pivot.M.Classic.R2 | Classic pivot R2 |
| Pivot.M.Classic.R3 | Classic pivot R3 |
| Pivot.M.Fibonacci.S3 | Fibonacci pivot S3 |
| Pivot.M.Fibonacci.S2 | Fibonacci pivot S2 |
| Pivot.M.Fibonacci.S1 | Fibonacci pivot S1 |
| Pivot.M.Fibonacci.Middle | Fibonacci pivot middle |
| Pivot.M.Fibonacci.R1 | Fibonacci pivot R1 |
| Pivot.M.Fibonacci.R2 | Fibonacci pivot R2 |
| Pivot.M.Fibonacci.R3 | Fibonacci pivot R3 |
| Pivot.M.Camarilla.S3 | Camarilla pivot S3 |
| Pivot.M.Camarilla.S2 | Camarilla pivot S2 |
| Pivot.M.Camarilla.S1 | Camarilla pivot S1 |
| Pivot.M.Camarilla.Middle | Camarilla pivot middle |
| Pivot.M.Camarilla.R1 | Camarilla pivot R1 |
| Pivot.M.Camarilla.R2 | Camarilla pivot R2 |
| Pivot.M.Camarilla.R3 | Camarilla pivot R3 |
| Pivot.M.Woodie.S3 | Woodie pivot S3 |
| Pivot.M.Woodie.S2 | Woodie pivot S2 |
| Pivot.M.Woodie.S1 | Woodie pivot S1 |
| Pivot.M.Woodie.Middle | Woodie pivot middle |
| Pivot.M.Woodie.R1 | Woodie pivot R1 |
| Pivot.M.Woodie.R2 | Woodie pivot R2 |
| Pivot.M.Woodie.R3 | Woodie pivot R3 |
| Pivot.M.Demark.S1 | DeMark pivot S1 |
| Pivot.M.Demark.Middle | DeMark pivot middle |
| Pivot.M.Demark.R1 | DeMark pivot R1 |

## Timeframes

These values are used by `Technicals`, `CandleStreamer`, and other timeframe-aware methods.

| Input | API code |
|-------|----------|
| `1m` | `1` |
| `5m` | `5` |
| `15m` | `15` |
| `30m` | `30` |
| `1h` | `60` |
| `2h` | `120` |
| `4h` | `240` |
| `1d` | `1D` |
| `1w` | `1W` |
| `1M` | `1M` |

## Languages

| Language | Code |
|----------|------|
| English | `en` |
| German | `de` |
| French | `fr` |
| Spanish | `es` |
| Italian | `it` |
| Portuguese | `pt` |
| Russian | `ru` |
| Japanese | `ja` |
| Korean | `ko` |
| Arabic | `ar` |
| Hindi | `hi` |
| Swedish | `sv` |
| Turkish | `tr` |
| Thai | `th` |
| Vietnamese | `vi` |
| Indonesian | `id` |
| Persian | `fa` |
| Chinese | `ch` |
| Malay | `ms` |
| Greek | `el` |
| Hebrew | `he` |

## News Areas

Used by `get_news_headlines(..., area=...)`.

| Input value | Code |
|-------------|------|
| `world` | `WLD` |
| `americas` | `AME` |
| `europe` | `EUR` |
| `asia` | `ASI` |
| `oceania` | `OCN` |
| `africa` | `AFR` |

## News Countries

Used by `get_news(..., market_country=[...])`.

| Code | Country/Region |
|------|----------------|
| AE | United Arab Emirates |
| AO | Angola |
| AR | Argentina |
| AT | Austria |
| AU | Australia |
| BD | Bangladesh |
| BE | Belgium |
| BG | Bulgaria |
| BH | Bahrain |
| BR | Brazil |
| BW | Botswana |
| CA | Canada |
| CH | Switzerland |
| CL | Chile |
| CN | China |
| CO | Colombia |
| CY | Cyprus |
| CZ | Czech Republic |
| DE | Germany |
| DK | Denmark |
| EE | Estonia |
| EG | Egypt |
| ES | Spain |
| ET | Ethiopia |
| EU | European Union |
| FI | Finland |
| FR | France |
| GB | United Kingdom |
| GH | Ghana |
| GR | Greece |
| HK | Hong Kong |
| HR | Croatia |
| HU | Hungary |
| ID | Indonesia |
| IE | Ireland |
| IL | Israel |
| IN | India |
| IS | Iceland |
| IT | Italy |
| JP | Japan |
| KE | Kenya |
| KR | South Korea |
| KW | Kuwait |
| LK | Sri Lanka |
| LT | Lithuania |
| LU | Luxembourg |
| LV | Latvia |
| MA | Morocco |
| MU | Mauritius |
| MW | Malawi |
| MX | Mexico |
| MY | Malaysia |
| MZ | Mozambique |
| NA | Namibia |
| NG | Nigeria |
| NL | Netherlands |
| NO | Norway |
| NZ | New Zealand |
| OM | Oman |
| PE | Peru |
| PH | Philippines |
| PK | Pakistan |
| PL | Poland |
| PT | Portugal |
| QA | Qatar |
| RO | Romania |
| RS | Serbia |
| RU | Russia |
| RW | Rwanda |
| SA | Saudi Arabia |
| SC | Seychelles |
| SE | Sweden |
| SG | Singapore |
| SI | Slovenia |
| SK | Slovakia |
| TH | Thailand |
| TN | Tunisia |
| TR | Turkey |
| TW | Taiwan |
| TZ | Tanzania |
| UA | Ukraine |
| UG | Uganda |
| US | United States |
| VE | Venezuela |
| VN | Vietnam |
| ZA | South Africa |
| ZM | Zambia |
| ZW | Zimbabwe |

## News Providers

Used by `get_news(..., provider=[...])` and `get_news_headlines(..., provider=...)`.

| Provider |
|----------|
| 99Bitcoins |
| acceswire |
| acn |
| barchart |
| beincrypto |
| bravenewcoin |
| chainwire |
| cme_group |
| coindar |
| coinmarketcal |
| coinpedia |
| cointelegraph |
| cryptobriefing |
| cryptonews |
| dow-jones |
| dpa_afx |
| eqs |
| etfcom |
| financemagnates |
| financewire |
| forexlive |
| globenewswire |
| gurufocus |
| investorplace |
| invezz |
| jcn |
| leverage_shares |
| macenews |
| market-watch |
| marketbeat |
| marketindex |
| miranda_partners |
| modular_finance |
| moneycontrol |
| nbd |
| newsbtc |
| pressetext |
| quartr |
| reuters |
| sharecast |
| smallcaps |
| stockstory |
| stocktwits |
| the_block |
| thenewswire |
| tmx_newsfile |
| trading-economics |
| tradingview |
| u_today |
| zacks |
| zawya |

## News Sectors

Used by `get_news(..., sector=[...])`.

| Sector |
|--------|
| Commercial Services |
| Communications |
| Consumer Durables |
| Consumer Non-Durables |
| Consumer Services |
| Distribution Services |
| Electronic Technology |
| Energy Minerals |
| Finance |
| Government |
| Health Services |
| Health Technology |
| Industrial Services |
| Miscellaneous |
| Non-Energy Minerals |
| Process Industries |
| Producer Manufacturing |
| Retail Trade |
| Technology Services |
| Transportation |
| Utilities |

## News Corporate Activities

Used by `get_news(..., corp_activity=[...])`.

| Activity | Description |
|----------|-------------|
| credit_ratings | Credit ratings |
| dividends | Dividends |
| earnings | Earnings |
| earnings_calls | Earnings calls |
| esg | ESG |
| insider_trading | Insider trading |
| ipo | IPO |
| management | Management changes |
| mergers_and_acquisitions | Mergers and acquisitions |
| ownership_changes | Ownership changes |
| recommendation | Recommendations |
| share_buybacks | Share buybacks |
| strategy_business_products | Strategy, business, and products |

## News Economic Categories

Used by `get_news(..., economic_category=[...])`.

| Category | Description |
|----------|-------------|
| business | Business |
| consumer | Consumer |
| gdp | GDP |
| government | Government |
| health | Health |
| housing | Housing |
| labor | Labor |
| money | Money |
| prices | Prices |
| taxes | Taxes |
| trade | Trade |

## News Asset Markets

Used by `get_news(..., market=[...])`.

| Market | Description |
|--------|-------------|
| bond | Bonds |
| corp_bond | Corporate bonds |
| crypto | Crypto |
| economic | Economic |
| etf | ETF |
| forex | Forex |
| futures | Futures |
| index | Indices |
| stock | Stocks |
