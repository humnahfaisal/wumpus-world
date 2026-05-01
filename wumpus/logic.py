"""
Propositional Logic Engine with CNF and Resolution Refutation.

This module implements:
- Literal representation (e.g., "P_2_3" positive, "~P_2_3" negative)
- Clause representation (frozenset of literals = disjunction)
- Knowledge Base (set of clauses = conjunction of disjunctions = CNF)
- Resolution refutation algorithm to prove queries
"""


def negate(literal):
    """Negate a literal. 'P_2_3' -> '~P_2_3', '~P_2_3' -> 'P_2_3'."""
    if literal.startswith('~'):
        return literal[1:]
    return '~' + literal


def resolve(clause1, clause2):
    """
    Apply the resolution rule to two clauses.
    Returns a set of resolvents (each a frozenset of literals).
    A resolvent is produced for each pair of complementary literals.
    Tautological resolvents (containing both l and ~l) are discarded.
    """
    resolvents = set()
    for literal in clause1:
        neg = negate(literal)
        if neg in clause2:
            # Complementary literals found — create resolvent
            resolvent = (clause1 - {literal}) | (clause2 - {neg})
            # Discard tautologies
            is_tautology = any(negate(lit) in resolvent for lit in resolvent)
            if not is_tautology:
                resolvents.add(frozenset(resolvent))
    return resolvents


def resolution_refutation(kb_clauses, query_literal):
    """
    Use Resolution Refutation to prove a query literal.

    To prove query_literal (e.g., '~P_2_3'):
      1. Add the negation of the query (P_2_3) to the KB
      2. Attempt to derive the empty clause (contradiction)
      3. If empty clause found → query is PROVEN TRUE

    Uses the Set-of-Support strategy for efficiency:
      Only resolve new (support) clauses against existing clauses.

    Returns:
        (is_proven: bool, inference_steps: int)
    """
    negated_query = negate(query_literal)
    all_clauses = set(kb_clauses)

    # Set of support starts with the negated query
    support = {frozenset({negated_query})}
    all_clauses.add(frozenset({negated_query}))

    inference_steps = 0
    max_steps = 8000  # Safety limit

    while support and inference_steps < max_steps:
        new_support = set()

        for s_clause in support:
            for clause in list(all_clauses):
                if s_clause == clause:
                    continue

                inference_steps += 1
                resolvents = resolve(s_clause, clause)

                for resolvent in resolvents:
                    if len(resolvent) == 0:
                        # Empty clause = contradiction = query is proven!
                        return True, inference_steps
                    if resolvent not in all_clauses:
                        new_support.add(resolvent)

                if inference_steps >= max_steps:
                    return False, inference_steps

        if not new_support:
            # No new clauses can be derived — cannot prove query
            return False, inference_steps

        all_clauses.update(new_support)
        support = new_support

    return False, inference_steps
