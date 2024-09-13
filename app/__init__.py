from flask import Flask, jsonify
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
from .routes import main

limiter = Limiter(
        get_remote_address,
        default_limits=["5 per 30 seconds"]
    )

def create_app():
    app = Flask(__name__, template_folder = './static/template', static_folder = './static')
    app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
    app.secret_key = 'jdybmhf5h*&@#$hjf^&8744ihefohoiwehf'
    load_dotenv()

    limiter.init_app(app)

    app.register_blueprint(main)

    @app.errorhandler(404)
    def not_found_error(error):
        response = jsonify({"message": "Page not found"})
        response.status_code = 404
        return response
    
    @app.errorhandler(500)
    def internal_error(error):
        response = jsonify({"message": "Internal server error"})
        response.status_code = 500
        return response
    
    # init rate limit for the recommendations requests
    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit_error():
        response = jsonify({
            "error": "Rate limit exceeded",
            "message": "The Spotify API imposes a rate limit on recommendation requests, please try again in 30 seconds"
        })
        response.status_code = 429
        response.headers["Retry-After"] = 30
        return response
    
    return app

my_app = create_app()