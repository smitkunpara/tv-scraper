import json

from tv_scraper.scrapers.social import News


def main():
    scraper = News()

    print("--- Fetching News for Symbol: XAUUSD ---")
    result = scraper.get_news(symbol="OANDA:XAUUSD", limit=5)
    print(json.dumps(result, indent=2))

    print("\n--- Fetching News with Country (US, IN) and Market (crypto) ---")
    result = scraper.get_news(market_country=["US", "IN"], market=["crypto"], limit=5)
    print(json.dumps(result, indent=2))

    print("\n--- Testing URL Length Limit (Adding many filters) ---")
    # This should probably trigger the 4096 character limit if we add enough items
    # But let's just add quite a few to see the URL construction
    result = scraper.get_news(
        market_country=[
            "AE",
            "AO",
            "AR",
            "AT",
            "AU",
            "BD",
            "BE",
            "BG",
            "BH",
            "BR",
            "BW",
            "CA",
            "CH",
            "CL",
            "CN",
            "CO",
            "CY",
            "CZ",
            "DE",
            "DK",
            "EE",
            "EG",
            "ES",
            "ET",
            "EU",
            "FI",
            "FR",
            "GB",
            "GH",
            "GR",
            "HK",
            "HR",
            "HU",
            "ID",
            "IE",
            "IL",
            "IN",
            "IS",
            "IT",
            "JP",
            "KE",
            "KR",
            "KW",
            "LK",
            "LT",
            "LU",
            "LV",
            "MA",
            "MU",
            "MW",
            "MX",
            "MY",
            "MZ",
            "NA",
            "NG",
            "NL",
            "NO",
            "NZ",
            "OM",
            "PE",
            "PH",
            "PK",
            "PL",
            "PT",
            "QA",
            "RO",
            "RS",
            "RU",
            "RW",
            "SA",
            "SC",
            "SE",
            "SG",
            "SI",
            "SK",
            "TH",
            "TN",
            "TR",
            "TW",
            "TZ",
            "UA",
            "UG",
            "US",
            "VE",
            "VN",
            "ZA",
            "ZM",
            "ZW",
        ],
        sector=["Electronic Technology", "Finance", "Technology Services", "Utilities"],
        limit=1,
    )
    print(f"Status: {result['status']}")
    if result["status"] == "failed":
        print(f"Error: {result['error']}")


if __name__ == "__main__":
    main()
