"""Assignment CRUD routes."""
import json
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..extensions import db
from ..models.assignment import Assignment, Rubric
from ..services.rubric_grader import get_default_rubric

assignments_bp = Blueprint('assignments', __name__, url_prefix='/assignments')


@assignments_bp.route('/')
@login_required
def list_assignments():
    assignments = Assignment.query.order_by(Assignment.created_at.desc()).all()
    return render_template('assignments/list.html', assignments=assignments)


@assignments_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        assignment_type = request.form.get('assignment_type', 'descriptive')
        language = request.form.get('language', '').strip() or None
        reference_solution = request.form.get('reference_solution', '').strip()
        due_date_str = request.form.get('due_date', '').strip()

        # Parse test cases
        test_cases_raw = request.form.get('test_cases', '[]')
        try:
            test_cases = json.loads(test_cases_raw)
        except json.JSONDecodeError:
            test_cases = []

        if not title:
            flash('Assignment title is required.', 'danger')
            return render_template('assignments/create.html')

        # Parse due date
        due_date = None
        if due_date_str:
            from datetime import datetime
            try:
                due_date = datetime.fromisoformat(due_date_str)
            except ValueError:
                pass

        assignment = Assignment(
            faculty_id=current_user.id,
            title=title,
            description=description,
            assignment_type=assignment_type,
            language=language,
            reference_solution=reference_solution,
            due_date=due_date
        )
        assignment.test_cases = test_cases
        db.session.add(assignment)
        db.session.flush()  # Get the ID

        # Parse rubric criteria
        criteria = request.form.getlist('rubric_criterion[]')
        weights = request.form.getlist('rubric_weight[]')
        descriptions = request.form.getlist('rubric_description[]')

        total_weight = 0
        if criteria and weights:
            for c, w, d in zip(criteria, weights, descriptions):
                if c.strip() and w.strip():
                    weight_val = float(w)
                    total_weight += weight_val
                    rubric = Rubric(
                        assignment_id=assignment.id,
                        criterion=c.strip(),
                        weight=weight_val,
                        description=d.strip() if d else None
                    )
                    db.session.add(rubric)
            
            if total_weight == 0:
                flash('Rubric weights cannot be zero.', 'danger')
                db.session.rollback()
                return render_template('assignments/create.html', default_rubric=get_default_rubric(assignment_type))
            
            if total_weight != 100:
                flash(f'Note: Rubric weights sum to {total_weight}%. They will be normalized to 100% during grading.', 'warning')
        else:
            # Add default rubric
            for r in get_default_rubric(assignment_type):
                rubric = Rubric(
                    assignment_id=assignment.id,
                    criterion=r['criterion'],
                    weight=r['weight'],
                    description=r.get('description')
                )
                db.session.add(rubric)

        db.session.commit()
        flash(f'Assignment "{title}" created successfully!', 'success')
        return redirect(url_for('assignments.detail', id=assignment.id))

    default_rubric = get_default_rubric('coding')
    return render_template('assignments/create.html', default_rubric=default_rubric)


@assignments_bp.route('/<int:id>')
@login_required
def detail(id):
    assignment = Assignment.query.get_or_404(id)
    submissions = assignment.submissions.order_by(
        db.text('submitted_at DESC')
    ).all()
    return render_template('assignments/detail.html',
                           assignment=assignment, submissions=submissions)


@assignments_bp.route('/<int:id>/evaluate-all', methods=['POST'])
@login_required
def evaluate_all(id):
    """Trigger evaluation for all pending submissions."""
    from ..routes.evaluation import perform_evaluation
    assignment = Assignment.query.get_or_404(id)
    pending = assignment.submissions.filter_by(status='pending').all()
    
    if not pending:
        flash('No pending submissions to evaluate.', 'info')
        return redirect(url_for('assignments.detail', id=id))
        
    count = 0
    errors = 0
    for sub in pending:
        try:
            success, _ = perform_evaluation(sub.id)
            if success:
                count += 1
            else:
                errors += 1
        except Exception as e:
            errors += 1
            print(f"Error evaluating submission {sub.id}: {str(e)}")
            
    flash(f'Batch evaluation complete: {count} successful, {errors} errors.', 
          'success' if errors == 0 else 'warning')
    return redirect(url_for('assignments.detail', id=id))


@assignments_bp.route('/<int:id>/release-grades', methods=['POST'])
@login_required
def release_grades(id):
    """Release grades for all evaluated submissions."""
    assignment = Assignment.query.get_or_404(id)
    submissions = assignment.submissions.filter_by(status='evaluated').all()
    
    for sub in submissions:
        sub.is_released = True
        
    db.session.commit()
    flash(f'Grades released for {len(submissions)} submissions.', 'success')
    return redirect(url_for('assignments.detail', id=id))


@assignments_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    assignment = Assignment.query.get_or_404(id)
    db.session.delete(assignment)
    db.session.commit()
    flash(f'Assignment "{assignment.title}" deleted.', 'info')
    return redirect(url_for('assignments.list_assignments'))
