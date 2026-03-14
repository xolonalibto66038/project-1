# recommendations/engine.py

# ── Weight configuration ───────────────────────────────────────────────────────
#
# Scoring philosophy:
#   - level_id    : hard constraint (enforced before scoring, not weighted)
#   - grade_id    : heaviest weight — wrong grade = nearly useless recommendation
#   - subject_id  : strong signal — must be same subject to be relevant
#   - specialty_id: Secondaire filter — SE resource shouldn't go to Lettres student
#                   NULL on both sides (non-Secondaire) is treated as a match
#   - course_id   : same course = highly related content
#   - term        : temporal relevance — student is studying T2 now, T1 is stale
#   - item_type   : weak signal — a lesson and an exercise are both useful
#   - difficulty  : small bonus for matching the student's current level
#
FEATURE_WEIGHTS = {
    "grade_id": 8,  # Wrong grade → nearly useless
    "subject_id": 6,  # Must be same subject to be meaningful
    "specialty_id": 4,  # Secondaire filière match (NULL/NULL counts as match)
    "course_id": 3,  # Same course → highly related
    "term": 2,  # Temporal relevance
    "item_type": 1,  # Weakest — cross-type recs still useful
    "difficulty": 1,  # Small bonus
}

MAX_POSSIBLE_SCORE = sum(FEATURE_WEIGHTS.values())  # 25


def compute_similarity(features_a: dict, features_b: dict) -> float:
    """
    Weighted attribute overlap between two feature dicts.

    Returns a normalised float in [0.0, 1.0].

    Hard constraints (return 0.0 immediately, no partial score):
      - Different level_id  → never recommend across education levels
      - Different grade_id  → never recommend across grades
        Exception: if *either* grade_id is None, skip this constraint so
        that partially-populated vectors don't get silently zeroed out.

    Specialty rule (not a hard constraint — partial credit applies):
      - If both items have a specialty set AND they differ → no specialty points
      - If either item has no specialty (NULL) → treat as "applies to all",
        award full specialty points (common case for non-Secondaire content)
    """
    # ── Hard constraints ───────────────────────────────────────────────────────
    level_a = features_a.get("level_id")
    level_b = features_b.get("level_id")
    if level_a is not None and level_b is not None and level_a != level_b:
        return 0.0

    grade_a = features_a.get("grade_id")
    grade_b = features_b.get("grade_id")
    if grade_a is not None and grade_b is not None and grade_a != grade_b:
        return 0.0

    # ── Weighted scoring ───────────────────────────────────────────────────────
    score = 0

    for feature, weight in FEATURE_WEIGHTS.items():
        val_a = features_a.get(feature)
        val_b = features_b.get(feature)

        if feature == "specialty_id":
            # NULL on either side → item applies to all specialties → full points
            # Both set and equal → full points
            # Both set and different → no points
            if val_a is None or val_b is None or val_a == val_b:
                score += weight
        else:
            # Standard rule: both must be set and equal to score
            if val_a is not None and val_b is not None and val_a == val_b:
                score += weight

    return round(score / MAX_POSSIBLE_SCORE, 4)


def rank_candidates(
    source_features: dict,
    candidates: list[tuple[any, dict]],  # list of (instance, feature_dict)
    limit: int = 6,
    min_score: float = 0.2,
) -> list[tuple[float, any]]:
    """
    Scores and ranks candidate (instance, features) pairs against the source.

    Args:
        source_features : feature dict of the reference item
        candidates      : list of (model_instance, feature_dict) to score
        limit           : maximum number of results to return
        min_score       : minimum similarity threshold (0.0 – 1.0)

    Returns:
        List of (score, instance) sorted by descending score, capped at `limit`.
    """
    scored = []
    for instance, features in candidates:
        score = compute_similarity(source_features, features)
        if score >= min_score:
            scored.append((score, instance))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:limit]
