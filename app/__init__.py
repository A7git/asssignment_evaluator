"""Application Factory for the Assignment Evaluation System."""
import os
from flask import Flask
from .extensions import db, migrate, login_manager
from .config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure instance and upload directory exist
    instance_path = os.path.join(app.root_path, '..', 'instance')
    upload_path = os.path.join(app.root_path, '..', app.config['UPLOAD_FOLDER'])
    
    os.makedirs(instance_path, exist_ok=True)
    os.makedirs(upload_path, exist_ok=True)
    
    # Configure logging
    import logging
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(os.path.join(instance_path, 'app.log'), maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Assignment Evaluator Startup')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.assignments import assignments_bp
    from .routes.submissions import submissions_bp
    from .routes.evaluation import evaluation_bp
    from .routes.dashboard import dashboard_bp
    from .routes.student import student_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(assignments_bp)
    app.register_blueprint(submissions_bp)
    app.register_blueprint(evaluation_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(student_bp)

    # Create tables and seed admin user
    with app.app_context():
        from . import models  # noqa: F401
        db.create_all()
        _seed_admin(app)

    @app.errorhandler(413)
    def request_entity_too_large(error):
        from flask import flash, redirect, request
        flash('The file is too large. Max size is 16MB.', 'danger')
        return redirect(request.referrer or url_for('dashboard.index')), 413

    return app


def _seed_admin(app):
    """Create default admin account if none exists."""
    from .models.user import User
    if not User.query.filter_by(role='faculty').first():
        admin = User(
            username='admin',
            email='admin@university.edu',
            full_name='System Administrator',
            role='faculty'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        app.logger.info('Default admin account created (admin / admin123)')
