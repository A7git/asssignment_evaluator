"""Rubric-based grading service."""


def apply_rubric(scores, rubrics):
    """Apply rubric weights to calculate final score.

    Args:
        scores: dict mapping criterion names to scores (0-100).
        rubrics: list of Rubric model instances or dicts with 'criterion' and 'weight'.

    Returns:
        float: Weighted final score (0-100).
    """
    if not rubrics:
        # No rubric defined — simple average
        if scores:
            return round(sum(scores.values()) / len(scores), 1)
        return 0.0

    total_weight = 0.0
    weighted_sum = 0.0

    for rubric in rubrics:
        criterion = rubric.criterion if hasattr(rubric, 'criterion') else rubric['criterion']
        weight = rubric.weight if hasattr(rubric, 'weight') else rubric['weight']

        score = _find_score(scores, criterion)
        weighted_sum += score * (weight / 100.0)
        total_weight += weight

    if total_weight == 0:
        return 0.0

    # Normalize if weights don't sum to 100
    if total_weight != 100:
        weighted_sum = weighted_sum * (100 / total_weight)

    return round(weighted_sum, 1)


def _find_score(scores, criterion):
    """Find a score matching a rubric criterion name.

    Maps common criterion names to score keys.
    """
    criterion_lower = criterion.lower()

    # Direct mapping
    mapping = {
        'correctness': ['correctness_score', 'correctness'],
        'style': ['style_score', 'style', 'code quality', 'code_quality'],
        'code quality': ['style_score', 'style'],
        'clarity': ['clarity_score', 'clarity', 'readability'],
        'readability': ['clarity_score', 'clarity'],
        'completeness': ['completeness_score', 'completeness'],
        'originality': ['plagiarism_score', 'originality', 'originality_score'],
        'plagiarism': ['plagiarism_score'],
        'similarity': ['similarity_score', 'similarity'],
        'grammar': ['grammar_score', 'grammar'],
        'formatting': ['formatting_score', 'formatting', 'style_score'],
        'efficiency': ['style_score', 'efficiency'],
    }

    for key, score_keys in mapping.items():
        if key in criterion_lower:
            for sk in score_keys:
                if sk in scores:
                    return scores[sk]

    # Fallback: try direct key match
    for key, value in scores.items():
        if criterion_lower in key.lower() or key.lower() in criterion_lower:
            return value

    # Default
    return 50.0


def get_default_rubric(assignment_type):
    """Return default rubric criteria for an assignment type."""
    if assignment_type == 'coding':
        return [
            {'criterion': 'Correctness', 'weight': 40.0, 'description': 'Test case pass rate'},
            {'criterion': 'Code Quality', 'weight': 25.0, 'description': 'Style, comments, structure'},
            {'criterion': 'Originality', 'weight': 20.0, 'description': 'Plagiarism-free work'},
            {'criterion': 'Efficiency', 'weight': 15.0, 'description': 'Code efficiency and best practices'},
        ]
    else:
        return [
            {'criterion': 'Correctness', 'weight': 30.0, 'description': 'Accuracy and relevance'},
            {'criterion': 'Clarity', 'weight': 25.0, 'description': 'Clear and readable writing'},
            {'criterion': 'Completeness', 'weight': 25.0, 'description': 'Coverage of required topics'},
            {'criterion': 'Originality', 'weight': 20.0, 'description': 'Original work, not plagiarized'},
        ]
