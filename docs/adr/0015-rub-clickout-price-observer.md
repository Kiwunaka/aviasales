# ADR 0015: RUB Click-Out Price Observer

Date: 2026-06-23

## Status

Accepted for the current backend slice.

## Context

The product does not need in-app booking, order creation, payment processing or ticket issuing. The desired flow is:

1. Find the cheapest visible prices across relevant sources.
2. Show source, freshness and caveats.
3. Send the user to an external aggregator or official carrier website to buy in RUB.

Official references checked on 2026-06-23:

- Travelpayouts Aviasales Data API: https://support.travelpayouts.com/hc/en-us/articles/203956163-Aviasales-Data-API
- Aviasales Search API access requirements: https://support.travelpayouts.com/hc/en-us/articles/210995808-How-to-get-access-to-the-Aviasales-Search-API
- Yandex Travel affiliate registration: https://yandex.com/support/travel-distr/en/partner/registration
- Yandex Travel partner links: https://yandex.com/support/travel-distr/en/instruments/partner-links

## Decision

1. Flight Hunter is a price observer and click-out product, not a booking product.
2. Every source is represented as a `PriceSource` with:
   - source type;
   - price kind;
   - RUB support;
   - external purchase flow;
   - manual confirmation requirement.
3. API and cached sources are separated from external partner links and carrier websites.
4. Scraping is not a default adapter. A future scraping observer can exist only behind a feature flag and per-source permission check.
5. The scraping observer policy blocks:
   - CAPTCHA solving;
   - stealth/fingerprint spoofing;
   - rotating/residential proxies;
   - reused cookies;
   - login-required/private pages;
   - background collection.
6. Any scraped/displayed fare is labelled `observed_price`, not guaranteed availability.

## Consequences

- The app can guide users toward cheaper RUB purchase options without storing payment data.
- RU aggregators and official carrier sites can appear as click-out sources even when no public API exists.
- Real live automation remains source-by-source work, not a generic hidden scraper.
- The user can explicitly opt into risky scraping later, but the codebase keeps hard guardrails.

## Verification

- `tests/unit/application/test_price_sources.py`
- `tests/unit/api/test_price_sources_api.py`
- `tests/unit/application/test_scraping_policy.py`
