from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from flight_hunter.ops.airport_import import run_import
from flight_hunter.persistence.models import mapper_registry
from flight_hunter.persistence.repositories import AirportReferenceRepository


def test_airport_import_cli_service_imports_local_csv(tmp_path) -> None:
    csv_path = tmp_path / "airports.csv"
    db_path = tmp_path / "flight-hunter.db"
    csv_path.write_text(
        "\n".join(
            (
                "id,ident,type,name,latitude_deg,longitude_deg,elevation_ft,continent,"
                "iso_country,iso_region,municipality,scheduled_service,gps_code,icao_code,"
                "iata_code,local_code,home_link,wikipedia_link,keywords",
                "1,EPWA,large_airport,Warsaw Chopin Airport,52.1657,20.9671,361,EU,"
                "PL,PL-MZ,Warsaw,yes,EPWA,EPWA,WAW,,,,",
            )
        ),
        encoding="utf-8",
    )

    result = asyncio.run(
        run_import(
            airports_csv=csv_path,
            database_url=f"sqlite+aiosqlite:///{db_path}",
        )
    )
    airports = asyncio.run(_search(db_path))

    assert result["status"] == "imported"
    assert result["rows_imported"] == 1
    assert [match.airport.iata_code for match in airports] == ["WAW"]


async def _search(db_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    async with engine.begin() as connection:
        await connection.run_sync(mapper_registry.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        return await AirportReferenceRepository(session).search("Warsaw")
