"""Feedback generation service."""


def generate_feedback(eval_results):
    """Generate detailed feedback based on evaluation results.

    Args:
        eval_results: dict with score fields and metadata.

    Returns:
        dict: {strengths, weaknesses, suggestions, summary}
    """
    strengths = []
    weaknesses = []
    suggestions = []

    correctness = eval_results.get('correctness_score', 0)
    style = eval_results.get('style_score', 0)
    similarity = eval_results.get('similarity_score', 0)
    clarity = eval_results.get('clarity_score', 0)
    completeness = eval_results.get('completeness_score', 0)
    plagiarism = eval_results.get('plagiarism_score', 100)
    is_code = eval_results.get('is_code', False)

    # Correctness feedback
    if correctness >= 90:
        strengths.append('Excellent correctness — nearly all test cases passed or content is highly accurate.')
    elif correctness >= 70:
        strengths.append('Good correctness with most requirements met.')
        suggestions.append('Review edge cases and boundary conditions to improve accuracy.')
    elif correctness >= 50:
        weaknesses.append('Moderate correctness — several issues found.')
        suggestions.append('Carefully re-read the problem statement and verify your solution against all requirements.')
    else:
        weaknesses.append('Low correctness score — significant issues in the submission.')
        suggestions.append('Consider revisiting the fundamentals and testing incrementally.')

    # Style / Code Quality
    if is_code:
        if style >= 85:
            strengths.append('Clean, well-structured code with good documentation.')
        elif style >= 60:
            suggestions.append('Add more comments and consider breaking long functions into smaller ones.')
        else:
            weaknesses.append('Code style needs improvement — inconsistent formatting or missing documentation.')
            suggestions.append('Follow PEP 8 (Python) / Google Style Guide. Add docstrings and comments.')
    else:
        if clarity >= 80:
            strengths.append('Clear, well-written prose with good grammar.')
        elif clarity >= 60:
            suggestions.append('Proofread for grammar errors and improve sentence structure.')
        else:
            weaknesses.append('Writing clarity needs improvement.')
            suggestions.append('Use shorter sentences, active voice, and proofread carefully.')

    # Completeness
    if completeness >= 85:
        strengths.append('Comprehensive coverage of all required topics.')
    elif completeness >= 60:
        suggestions.append('Some topics were not fully addressed — ensure all rubric criteria are covered.')
    else:
        weaknesses.append('Incomplete submission — several key areas were not addressed.')
        suggestions.append('Review the assignment rubric and ensure each criterion is explicitly addressed.')

    # Plagiarism
    if plagiarism >= 90:
        strengths.append('Highly original work with no significant similarities to peers.')
    elif plagiarism >= 70:
        suggestions.append('Some similarities detected — ensure proper citations and original phrasing.')
    else:
        weaknesses.append('Significant similarity detected with peer submissions.')
        suggestions.append('Rewrite flagged sections in your own words. Add proper citations where needed.')

    # Summary
    final = eval_results.get('final_score', 0)
    if final >= 85:
        summary = 'Outstanding submission! Keep up the excellent work.'
    elif final >= 70:
        summary = 'Good work with room for improvement in a few areas.'
    elif final >= 55:
        summary = 'Acceptable submission but several areas need attention.'
    else:
        summary = 'This submission needs significant revision. Please review the feedback carefully.'

    return {
        'strengths': strengths,
        'weaknesses': weaknesses,
        'suggestions': suggestions,
        'summary': summary
    }
