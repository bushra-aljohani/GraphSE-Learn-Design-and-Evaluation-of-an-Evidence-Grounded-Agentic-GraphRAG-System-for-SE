"""GraphSE-Learn: provenance validation, assessment grading, and learner modeling.

Source-span verification, deterministic answer-key grading, and standard
Bayesian Knowledge Tracing. See README.md for the shared code's scope.
Run with Python 3.10+: python example.py
"""
from __future__ import annotations

import json


def provenance_check(source: dict, proposal: dict) -> bool:
    """Check a source ID, page range, and whitespace-normalized verbatim span.

    Traceability does not establish semantic correctness or completeness.
    """
    span = proposal.get("span")
    page = proposal.get("page")
    if not isinstance(span, str) or not span.strip() or type(page) is not int:
        return False
    normalize = lambda text: " ".join(text.split())
    return (
        proposal.get("chunk_id") == source["chunk_id"]
        and source["page_start"] <= page <= source["page_end"]
        and normalize(span) in normalize(source["text"])
    )


def grade(answer: str, key: str, options: tuple[str, ...]) -> bool | None:
    """Grade a stored answer key; an unsure response supplies no graded evidence."""
    if key not in options:
        raise ValueError("Answer key must be a valid option")
    if answer == "unsure":
        return None
    if answer not in options:
        raise ValueError("Answer must be a valid option or 'unsure'")
    return answer == key


def update_mastery(prior: float, outcome: bool | None) -> float:
    """Standard BKT with the manuscript's pilot T=.30, G=.20, S=.10.

    Apply the learning transition after either graded outcome. Unsure, dialogue,
    and lesson views are not graded outcomes and must not update mastery.
    """
    if not 0.0 <= prior <= 1.0:
        raise ValueError("Mastery probability must be in [0, 1]")
    if outcome is None:
        return prior
    if type(outcome) is not bool:
        raise ValueError("Outcome must be True, False, or None")
    transit, guess, slip = 0.30, 0.20, 0.10
    if outcome:
        numerator = prior * (1 - slip)
        posterior = numerator / (numerator + (1 - prior) * guess)
    else:
        numerator = prior * slip
        posterior = numerator / (numerator + (1 - prior) * (1 - guess))
    return posterior + (1 - posterior) * transit


def main() -> None:
    # Author-written synthetic text, not a passage from SWEBOK.
    source = {
        "chunk_id": "synthetic-1", "page_start": 1, "page_end": 1,
        "text": "A focused module groups responsibilities that belong together.",
    }
    proposal = {
        "chunk_id": "synthetic-1", "page": 1,
        "span": "A focused module groups responsibilities that belong together.",
    }
    if not provenance_check(source, proposal):
        print("No verified evidence: decline without generation.")
        return
    # Static example item; not generated, expert-reviewed, or a research item.
    print("Synthetic question: Which description matches the supplied passage?")
    print("A: Group related responsibilities. B: Mix unrelated responsibilities.")
    prior = 0.30
    outcome = grade("A", key="A", options=("A", "B"))
    mastery = update_mastery(prior, outcome)
    print(json.dumps({
        "source": "synthetic-1, page 1", "provenance_passed": True,
        "illustrative_answer": "A", "correct": outcome,
        "mastery_before": prior, "mastery_after": round(mastery, 6),
        "mastered": mastery >= 0.95,
        "unsure_leaves_mastery_unchanged": update_mastery(mastery, None) == mastery,
    }, indent=2))


if __name__ == "__main__":
    main()
