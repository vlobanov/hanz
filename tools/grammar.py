from langchain_core.tools import tool
from database import (
    add_concept,
    update_concept,
    get_all_concepts,
    mark_mastered,
)


@tool
async def save_grammar_concept(
    concept: str, notes: str = None, examples: str = None
) -> str:
    """Save a new grammar concept to track for the student.

    Use this when the student encounters a new grammar topic they should learn,
    such as "Akkusativ", "Perfekt tense", "Modalverben", etc.

    Args:
        concept: The name of the grammar concept (e.g., "Akkusativ", "Perfekt")
        notes: Optional notes about this concept
        examples: Optional example sentences demonstrating the concept
    """
    concept_id = await add_concept(concept, notes, examples)
    return f"Grammar concept '{concept}' saved with ID {concept_id}. Status: learning."


@tool
async def update_grammar_concept(
    concept_name: str, status: str = None, notes: str = None, examples: str = None
) -> str:
    """Update an existing grammar concept's status or notes.

    Use this to track progress on a grammar concept or add new notes/examples.

    Args:
        concept_name: The name of the concept to update (partial match supported)
        status: New status - one of: 'learning', 'practicing', 'mastered'
        notes: Updated notes about this concept
        examples: Updated example sentences
    """
    if status and status not in ["learning", "practicing", "mastered"]:
        return f"Invalid status '{status}'. Use: learning, practicing, or mastered."

    success = await update_concept(
        concept_name=concept_name, status=status, notes=notes, examples=examples
    )
    if success:
        return f"Updated grammar concept '{concept_name}'."
    return f"Could not find grammar concept matching '{concept_name}'."


@tool
async def list_grammar_concepts() -> str:
    """List all tracked grammar concepts with their status.

    Use this to see what grammar topics the student is working on.
    Returns a formatted list of all concepts with their status and notes.
    """
    concepts = await get_all_concepts()
    if not concepts:
        return "No grammar concepts tracked yet."

    result = "Grammar concepts:\n\n"
    for c in concepts:
        status_emoji = {"learning": "📚", "practicing": "🔄", "mastered": "✅"}.get(
            c["status"], "📚"
        )
        result += f"{status_emoji} **{c['concept']}** ({c['status']})\n"
        if c["notes"]:
            result += f"   Notes: {c['notes']}\n"
        if c["examples"]:
            result += f"   Examples: {c['examples']}\n"
        result += "\n"

    return result


@tool
async def mark_concept_mastered(concept_name: str) -> str:
    """Mark a grammar concept as mastered.

    Use this when the student has demonstrated solid understanding of a concept.

    Args:
        concept_name: The name of the concept to mark as mastered
    """
    success = await mark_mastered(concept_name=concept_name)
    if success:
        return f"Congratulations! '{concept_name}' marked as mastered! 🎉"
    return f"Could not find grammar concept matching '{concept_name}'."


def get_grammar_tools():
    """Return all grammar-related tools for the agent."""
    return [
        save_grammar_concept,
        update_grammar_concept,
        list_grammar_concepts,
        mark_concept_mastered,
    ]
