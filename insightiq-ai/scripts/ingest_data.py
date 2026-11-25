"""CLI Script to Run the Data Ingestion Pipeline.

Usage:
    python scripts/ingest_data.py [--data-dir data/raw] [--db-url sqlite:///data/insightiq.db]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from sqlalchemy.orm import sessionmaker

# Add backend to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.config import settings
from app.database.connection import get_engine
from app.database.session import db_context, init_db
from app.data_processing.ingestion import IngestionPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest raw e-commerce data into InsightIQ database.")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=str(Path(__file__).resolve().parent.parent / "data" / "raw"),
        help="Path to directory containing raw CSV files.",
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="Database URL override (e.g. postgresql://... or sqlite:///data/insightiq.db).",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    db_url = args.db_url or settings.DATABASE_URL

    print(f"==================================================")
    print(f" InsightIQ AI - Data Ingestion Pipeline")
    print(f" Source Directory: {data_dir.resolve()}")
    print(f" Target Database:  {db_url.split('@')[-1] if '@' in db_url else db_url}")
    print(f"==================================================\n")

    if not data_dir.exists():
        print(f"Error: Data directory does not exist: {data_dir}", file=sys.stderr)
        sys.exit(1)

    print("Step 1: Connecting to database and creating tables if missing...")
    engine = get_engine(db_url)
    init_db(engine)

    custom_sessionmaker = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    print("Step 2: Executing cleaning, validation, and ingestion pipeline...")
    pipeline = IngestionPipeline(data_dir=data_dir)

    try:
        with db_context(custom_sessionmaker=custom_sessionmaker) as session:
            summary = pipeline.run(session)

        print("\n" + summary.to_markdown())
        print("\nIngestion completed successfully!")
        sys.exit(0)

    except Exception as exc:
        print(f"\nIngestion failed with error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
