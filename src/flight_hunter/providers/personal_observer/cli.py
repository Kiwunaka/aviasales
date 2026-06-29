from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import NoReturn

from flight_hunter.config import AppSettings, load_env_file
from flight_hunter.domain.offers import SearchIntent
from flight_hunter.providers.personal_observer.runner import (
    PersonalObserverConfig,
    PersonalObserverError,
    PersonalObserverRunner,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="flight-hunter-observe",
        description="Run a user-action Personal Browser Observer check.",
    )
    parser.add_argument("--source", required=True)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--depart", required=True)
    parser.add_argument("--return-date", default=None)
    parser.add_argument("--passengers", type=int, default=1)
    parser.add_argument("--adults", type=int, default=None)
    parser.add_argument("--children", type=int, default=0)
    parser.add_argument("--infants", type=int, default=0)
    parser.add_argument("--currency", default="RUB")
    parser.add_argument("--fixture-html", type=Path, default=None)
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()

    load_env_file()
    settings = AppSettings.from_env()
    runner = PersonalObserverRunner(config=PersonalObserverConfig.from_settings(settings))
    intent = SearchIntent(
        origin=args.origin,
        destination=args.destination,
        departure_date=args.depart,
        return_date=args.return_date,
        passengers=args.passengers,
        adults=args.adults,
        children=args.children,
        infants=args.infants,
        currency=args.currency,
    )
    try:
        result = runner.observe(
            source_id=args.source,
            intent=intent,
            user_action=args.interactive,
            fixture_html_path=args.fixture_html,
        )
    except PersonalObserverError as exc:
        _exit_with_error(exc)

    print(
        json.dumps(
            {
                "source_id": result.source_id,
                "final_url": result.final_url,
                "confidence": result.extraction.confidence.value,
                "warnings": list(result.extraction.warnings),
                "offers": [
                    {
                        "origin": offer.origin,
                        "destination": offer.destination,
                        "departure_date": offer.departure_date,
                        "return_date": offer.return_date,
                        "amount_minor": (
                            offer.total_price.minor_units if offer.total_price is not None else None
                        ),
                        "currency": (
                            offer.total_price.currency if offer.total_price is not None else None
                        ),
                        "observed_at": offer.observed_at.isoformat(),
                        "freshness": offer.freshness.value,
                        "parser_version": offer.parser_version,
                        "parser_warnings": list(offer.parser_warnings),
                        "requires_external_confirmation": offer.requires_external_confirmation,
                    }
                    for offer in result.extraction.offers
                ],
            },
            ensure_ascii=False,
        )
    )


def _exit_with_error(error: PersonalObserverError) -> NoReturn:
    print(
        json.dumps(
            {"code": error.code.value, "message": error.message},
            ensure_ascii=False,
        )
    )
    raise SystemExit(2)
