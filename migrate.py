#!/usr/bin/env python3
"""
Simple database migration tool.

Usage:
    uv run python migrate.py          # Run all pending migrations
    uv run python migrate.py status   # Show migration status
    uv run python migrate.py reset    # Drop all tables and re-run migrations
"""

import asyncio
import sys
from pathlib import Path

import asyncpg

from config import POSTGRES_URL

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


async def get_connection():
    """Get database connection."""
    if not POSTGRES_URL:
        raise ValueError("POSTGRES_URL not set in environment")
    return await asyncpg.connect(POSTGRES_URL)


async def ensure_migrations_table(conn):
    """Create migrations tracking table if it doesn't exist."""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)


async def get_applied_migrations(conn) -> set[str]:
    """Get set of already applied migration names."""
    rows = await conn.fetch("SELECT name FROM _migrations ORDER BY name")
    return {row["name"] for row in rows}


async def get_pending_migrations(conn) -> list[Path]:
    """Get list of pending migration files."""
    applied = await get_applied_migrations(conn)

    migrations = []
    for f in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if f.name not in applied:
            migrations.append(f)

    return migrations


async def run_migration(conn, migration_file: Path):
    """Run a single migration file."""
    sql = migration_file.read_text()

    async with conn.transaction():
        await conn.execute(sql)
        await conn.execute(
            "INSERT INTO _migrations (name) VALUES ($1)",
            migration_file.name
        )

    print(f"  ✓ {migration_file.name}")


async def migrate():
    """Run all pending migrations."""
    conn = await get_connection()
    try:
        await ensure_migrations_table(conn)
        pending = await get_pending_migrations(conn)

        if not pending:
            print("No pending migrations.")
            return

        print(f"Running {len(pending)} migration(s)...")
        for migration_file in pending:
            await run_migration(conn, migration_file)

        print("Done!")
    finally:
        await conn.close()


async def status():
    """Show migration status."""
    conn = await get_connection()
    try:
        await ensure_migrations_table(conn)

        applied = await get_applied_migrations(conn)
        all_files = sorted(f.name for f in MIGRATIONS_DIR.glob("*.sql"))

        print("Migration status:")
        for name in all_files:
            status = "✓ applied" if name in applied else "○ pending"
            print(f"  {status}: {name}")

        if not all_files:
            print("  No migration files found.")
    finally:
        await conn.close()


async def reset():
    """Drop all tables and re-run migrations."""
    conn = await get_connection()
    try:
        # Get all tables
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
        """)

        if tables:
            print("Dropping tables...")
            for row in tables:
                await conn.execute(f'DROP TABLE IF EXISTS "{row["tablename"]}" CASCADE')
                print(f"  ✓ dropped {row['tablename']}")

        print("\nRunning migrations...")
        await ensure_migrations_table(conn)
        pending = await get_pending_migrations(conn)

        for migration_file in pending:
            await run_migration(conn, migration_file)

        print("Done!")
    finally:
        await conn.close()


async def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "migrate"

    if command == "migrate":
        await migrate()
    elif command == "status":
        await status()
    elif command == "reset":
        confirm = input("This will DELETE ALL DATA. Type 'yes' to confirm: ")
        if confirm == "yes":
            await reset()
        else:
            print("Aborted.")
    else:
        print(f"Unknown command: {command}")
        print("Usage: migrate.py [migrate|status|reset]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
