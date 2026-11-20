import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from db import db, init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS for React frontend
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Initialize Database & JWT
    init_db(app)
    jwt = JWTManager(app)

    @jwt.unauthorized_loader
    def unauthorized_callback(callback):
        return jsonify({
            'success': False,
            'message': 'Missing or invalid authentication token.'
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(callback):
        return jsonify({
            'success': False,
            'message': 'The provided token is invalid or malformed.'
        }), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'message': 'Authentication token has expired. Please log in again.'
        }), 401

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.attendance import attendance_bp
    from routes.exams import exams_bp
    from routes.assignments import assignments_bp
    from routes.activities import activities_bp
    from routes.planner import planner_bp
    from routes.timer import timer_bp
    from routes.notifications import notifications_bp
    from routes.documents import documents_bp
    from routes.chat import chat_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(attendance_bp, url_prefix='/api/attendance')
    app.register_blueprint(exams_bp, url_prefix='/api/exams')
    app.register_blueprint(assignments_bp, url_prefix='/api/assignments')
    app.register_blueprint(activities_bp, url_prefix='/api/activities')
    app.register_blueprint(planner_bp, url_prefix='/api/planner')
    app.register_blueprint(timer_bp, url_prefix='/api/timer')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(documents_bp, url_prefix='/api/documents')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    # Health check
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'system': 'Multilingual Academic Information Assistant',
            'timezone': Config.TIMEZONE_STR,
            'database': app.config['SQLALCHEMY_DATABASE_URI'].split('://')[0]
        }), 200

    # General Error Handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'success': False, 'message': 'Bad request.'}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'success': False, 'message': 'The requested resource was not found.'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'success': False, 'message': 'Internal server error.'}), 500

    # Start APScheduler (unless disabled for testing or cli tools)
    if not app.config.get('TESTING', False) and not os.environ.get('SEEDING') and not os.environ.get('FLASK_CLI_INVOCATION'):
        from services.scheduler_service import init_scheduler
        try:
            init_scheduler(app)
        except Exception as e:
            logger.warning(f"Scheduler initialization note: {e}")

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
