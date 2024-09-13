from flask import Flask
from dotenv import load_dotenv
from .routes import main

def create_app():
    app = Flask(__name__, template_folder = './static/template', static_folder = './static')
    app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
    app.secret_key = 'jdybmhf5h*&@#$hjf^&8744ihefohoiwehf'
    load_dotenv()

    app.register_blueprint(main)

    @app.errorhandler(404)
    def not_found_error(error):
        return "Page not found", 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return "Internal server error", 500
    
    return app

my_app = create_app()