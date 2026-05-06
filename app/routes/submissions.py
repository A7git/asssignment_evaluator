"""Submission upload routes."""
import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from ..extensions import db
from ..models.assignment import Assignment
from ..models.submission import Submission
from ..services.file_parser import parse_file

submissions_bp = Blueprint('submissions', __name__)


@submissions_bp.route('/submit/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
def upload(assignment_id):
    """Student upload page — links to student account."""
    if current_user.role != 'student':
        flash('Only students can upload submissions.', 'warning')
        return redirect(url_for('assignments.detail', id=assignment_id))

    assignment = Assignment.query.get_or_404(assignment_id)

    if request.method == 'POST':
        student_id = current_user.student_id or request.form.get('student_id', '').strip()
        student_name = current_user.full_name
        file = request.files.get('submission_file')

        if not student_id:
            flash('Student ID is missing from your profile.', 'danger')
            return render_template('submissions/upload.html', assignment=assignment)

        if not file or file.filename == '':
            flash('Please select a file to upload.', 'danger')
            return render_template('submissions/upload.html', assignment=assignment)

        # Validate file extension
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        allowed = set()
        for exts in current_app.config['ALLOWED_EXTENSIONS'].values():
            allowed |= exts

        if ext not in allowed:
            flash(f'File type .{ext} is not supported. Allowed: {", ".join(sorted(allowed))}', 'danger')
            return render_template('submissions/upload.html', assignment=assignment)

        # Save file with unique name
        upload_dir = os.path.join(current_app.root_path, '..', current_app.config['UPLOAD_FOLDER'])
        os.makedirs(upload_dir, exist_ok=True)

        unique_name = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = os.path.join(upload_dir, unique_name)
        file.save(file_path)

        # Extract text
        extracted_text = parse_file(file_path)

        submission = Submission(
            assignment_id=assignment_id,
            user_id=current_user.id,
            student_id=student_id,
            student_name=student_name,
            file_path=unique_name,
            file_name=file.filename,
            file_type=ext,
            extracted_text=extracted_text,
            status='pending'
        )
        db.session.add(submission)
        db.session.commit()

        flash('Submission uploaded successfully! Your work will be evaluated shortly.', 'success')
        return render_template('submissions/success.html',
                               assignment=assignment, submission=submission)

    return render_template('submissions/upload.html', assignment=assignment)


@submissions_bp.route('/submissions/<int:id>')
@login_required
def detail(id):
    """Faculty view of a submission."""
    submission = Submission.query.get_or_404(id)
    return render_template('submissions/detail.html', submission=submission)
