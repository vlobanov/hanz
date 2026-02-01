import aiosqlite
from datetime import datetime
from config import DATABASE_PATH


async def init_database():
    """Initialize the database and create tables if they don't exist."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS grammar_concepts (
                id INTEGER PRIMARY KEY,
                concept TEXT NOT NULL,
                status TEXT DEFAULT 'learning',
                notes TEXT,
                examples TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        await db.commit()


async def add_concept(concept: str, notes: str = None, examples: str = None) -> int:
    """Add a new grammar concept to track."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        now = datetime.now().isoformat()
        cursor = await db.execute(
            """
            INSERT INTO grammar_concepts (concept, notes, examples, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (concept, notes, examples, now, now),
        )
        await db.commit()
        return cursor.lastrowid


async def update_concept(
    concept_id: int = None,
    concept_name: str = None,
    status: str = None,
    notes: str = None,
    examples: str = None,
) -> bool:
    """Update an existing grammar concept by ID or name."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Find the concept
        if concept_id:
            cursor = await db.execute(
                "SELECT id FROM grammar_concepts WHERE id = ?", (concept_id,)
            )
        elif concept_name:
            cursor = await db.execute(
                "SELECT id FROM grammar_concepts WHERE concept LIKE ?",
                (f"%{concept_name}%",),
            )
        else:
            return False

        row = await cursor.fetchone()
        if not row:
            return False

        concept_id = row[0]
        now = datetime.now().isoformat()

        updates = []
        values = []

        if status:
            updates.append("status = ?")
            values.append(status)
        if notes:
            updates.append("notes = ?")
            values.append(notes)
        if examples:
            updates.append("examples = ?")
            values.append(examples)

        if not updates:
            return False

        updates.append("updated_at = ?")
        values.append(now)
        values.append(concept_id)

        await db.execute(
            f"UPDATE grammar_concepts SET {', '.join(updates)} WHERE id = ?",
            values,
        )
        await db.commit()
        return True


async def get_all_concepts() -> list[dict]:
    """Get all grammar concepts."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM grammar_concepts ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_concept_by_name(name: str) -> dict | None:
    """Get a concept by name (partial match)."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM grammar_concepts WHERE concept LIKE ?", (f"%{name}%",)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def mark_mastered(concept_id: int = None, concept_name: str = None) -> bool:
    """Mark a concept as mastered."""
    return await update_concept(
        concept_id=concept_id, concept_name=concept_name, status="mastered"
    )
