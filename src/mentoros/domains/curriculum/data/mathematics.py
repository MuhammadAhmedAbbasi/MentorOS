"""MentorOS v0.1 mathematics curriculum: 10 topics in two tiers.

Pure data. Loaded by `mentoros.domains.curriculum.seed`.
"""

from __future__ import annotations

from mentoros.domains.curriculum.seed import SubjectSpec, TopicSpec

MATHEMATICS = SubjectSpec(
    code="math",
    name="Mathematics",
    topics=[
        # ── Tier 1: Foundations ─────────────────────────────────────
        TopicSpec(
            code="arithmetic",
            name="Arithmetic",
            difficulty=1,
            description="Addition, subtraction, multiplication, division, order of operations.",
        ),
        TopicSpec(
            code="fractions",
            name="Fractions",
            difficulty=2,
            description="Equivalent fractions, simplifying, and the four operations on fractions.",
            prerequisites=["arithmetic"],
        ),
        TopicSpec(
            code="decimals",
            name="Decimals",
            difficulty=2,
            description="Place value, decimal operations, converting between decimals and fractions.",
            prerequisites=["arithmetic"],
        ),
        TopicSpec(
            code="percentages",
            name="Percentages",
            difficulty=3,
            description="Percent of a quantity, percent change, converting percents.",
            prerequisites=["fractions", "decimals"],
        ),
        TopicSpec(
            code="basic_algebra",
            name="Basic Algebra",
            difficulty=3,
            description="Variables, expressions, combining like terms, the distributive property.",
            prerequisites=["arithmetic"],
        ),
        # ── Tier 2: Intermediate ────────────────────────────────────
        TopicSpec(
            code="linear_equations",
            name="Linear Equations",
            difficulty=4,
            description="Solving one-variable linear equations.",
            prerequisites=["basic_algebra"],
        ),
        TopicSpec(
            code="systems_of_equations",
            name="Systems of Equations",
            difficulty=6,
            description="Solving two linear equations by substitution and elimination.",
            prerequisites=["linear_equations"],
        ),
        TopicSpec(
            code="factoring",
            name="Factoring",
            difficulty=5,
            description="Common factors, factoring trinomials, difference of squares.",
            prerequisites=["basic_algebra"],
        ),
        TopicSpec(
            code="quadratic_equations",
            name="Quadratic Equations",
            difficulty=7,
            description="Solving quadratics by factoring and the quadratic formula.",
            prerequisites=["factoring", "linear_equations"],
        ),
        TopicSpec(
            code="functions",
            name="Functions",
            difficulty=6,
            description="Function notation, domain and range, linear functions and graphs.",
            prerequisites=["linear_equations"],
        ),
    ],
)
