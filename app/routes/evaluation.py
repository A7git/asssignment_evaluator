"""Evaluation routes — trigger evaluation and view reports."""
import json
from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response
from flask_login import login_required
from ..extensions import db
from ..models.submission import Submission
from ..models.evaluation import Evaluation
from ..services.code_runner import run_code, analyze_code_style
from ..services.nlp_evaluator import (evaluate_similarity, evaluate_grammar,
                                       evaluate_completeness, evaluate_clarity)
from ..services.plagiarism import check_plagiarism
from ..services.rubric_grader import apply_rubric
from ..services.feedback_generator import generate_feedback

evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/evaluation')


@evaluation_bp.route('/evaluate/<int:submission_id>', methods=['POST'])
@login_required
def evaluate(submission_id):
    """Trigger the full evaluation pipeline for a submission."""
    success, message = perform_evaluation(submission_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('evaluation.report', submission_id=submission_id))


def perform_evaluation(submission_id):
    """Business logic for evaluating a submission."""
    submission = Submission.query.get(submission_id)
    if not submission:
        return False, "Submission not found."
        
    assignment = submission.assignment

    # Remove existing evaluation if re-evaluating
    if submission.evaluation:
        db.session.delete(submission.evaluation)
        db.session.flush()

    submission.status = 'evaluating'
    db.session.commit()

    try:
        scores = {}

        if assignment.is_coding:
            scores = _evaluate_coding(submission, assignment)
        else:
            scores = _evaluate_descriptive(submission, assignment)

        # Plagiarism check (peer comparison)
        peer_subs = Submission.query.filter(
            Submission.assignment_id == assignment.id,
            Submission.id != submission.id,
            Submission.extracted_text.isnot(None)
        ).all()

        peer_data = [{'student_id': p.student_id, 'student_name': p.student_name,
                       'text': p.extracted_text} for p in peer_subs]
        plag_result = check_plagiarism(submission.extracted_text or '', peer_data)
        scores['plagiarism_score'] = plag_result['originality_score']

        # Apply rubric
        final_score = apply_rubric(scores, assignment.rubrics)

        # Generate feedback
        feedback_input = {**scores, 'final_score': final_score,
                          'is_code': assignment.is_coding}
        feedback = generate_feedback(feedback_input)

        # Create evaluation record
        evaluation = Evaluation(
            submission_id=submission.id,
            correctness_score=scores.get('correctness_score', 0),
            style_score=scores.get('style_score', 0),
            similarity_score=scores.get('similarity_score', 0),
            clarity_score=scores.get('clarity_score', 0),
            completeness_score=scores.get('completeness_score', 0),
            plagiarism_score=plag_result['originality_score'],
            final_score=final_score,
            strengths='\n'.join(feedback['strengths']),
            weaknesses='\n'.join(feedback['weaknesses']),
            suggestions='\n'.join(feedback['suggestions']),
        )
        evaluation.feedback = feedback
        evaluation.plagiarism_details = plag_result
        evaluation.test_results = scores.get('test_results', [])

        db.session.add(evaluation)
        submission.status = 'evaluated'
        db.session.commit()

        return True, "Evaluation completed successfully!"

    except Exception as e:
        submission.status = 'error'
        db.session.commit()
        import traceback
        traceback.print_exc()
        return False, f"Evaluation failed: {str(e)}"


@evaluation_bp.route('/report/<int:submission_id>')
@login_required
def report(submission_id):
    """View the evaluation report for a submission."""
    submission = Submission.query.get_or_404(submission_id)
    return render_template('evaluation/report.html', submission=submission)


@evaluation_bp.route('/export/<int:submission_id>')
@login_required
def export_html(submission_id):
    """Export evaluation report as downloadable HTML."""
    submission = Submission.query.get_or_404(submission_id)
    html = render_template('evaluation/export.html', submission=submission)
    response = make_response(html)
    response.headers['Content-Type'] = 'text/html'
    response.headers['Content-Disposition'] = (
        f'attachment; filename=report_{submission.student_id}.html'
    )
    return response


def _evaluate_coding(submission, assignment):
    """Run coding assignment evaluation pipeline."""
    scores = {}
    code = submission.extracted_text or ''

    # Run test cases
    test_cases = assignment.test_cases
    if test_cases:
        result = run_code(assignment.language, code, test_cases)
        correctness = (result['passed'] / max(result['total'], 1)) * 100
        scores['correctness_score'] = round(correctness, 1)
        scores['test_results'] = result.get('results', [])
    else:
        # No test cases — use similarity to reference
        if assignment.reference_solution:
            scores['correctness_score'] = evaluate_similarity(code, assignment.reference_solution)
        else:
            scores['correctness_score'] = 50.0
        scores['test_results'] = []

    # Static analysis
    style_score, style_issues = analyze_code_style(code, assignment.language or 'python')
    scores['style_score'] = style_score
    scores['style_issues'] = style_issues

    # Similarity to reference
    if assignment.reference_solution:
        scores['similarity_score'] = evaluate_similarity(code, assignment.reference_solution)
    else:
        scores['similarity_score'] = scores['correctness_score']

    scores['clarity_score'] = style_score
    scores['completeness_score'] = scores.get('similarity_score', 50)

    return scores


def _evaluate_descriptive(submission, assignment):
    """Run descriptive assignment evaluation pipeline."""
    scores = {}
    text = submission.extracted_text or ''
    reference = assignment.reference_solution or ''

    # Semantic similarity to reference
    if reference:
        scores['similarity_score'] = evaluate_similarity(text, reference)
        scores['correctness_score'] = scores['similarity_score']
    else:
        scores['similarity_score'] = 50.0
        scores['correctness_score'] = 50.0

    # Grammar analysis
    grammar_score, grammar_issues = evaluate_grammar(text)
    scores['grammar_score'] = grammar_score
    scores['grammar_issues'] = grammar_issues

    # Clarity / readability
    scores['clarity_score'] = evaluate_clarity(text)

    # Completeness
    comp_score, comp_details = evaluate_completeness(text, reference)
    scores['completeness_score'] = comp_score
    scores['completeness_details'] = comp_details

    # Style is grammar + clarity
    scores['style_score'] = round((grammar_score + scores['clarity_score']) / 2, 1)

    return scores
