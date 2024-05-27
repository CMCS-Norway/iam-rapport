from flask import Flask, redirect, url_for, session, request, render_template
from config import Config
from models import db, User, Customer, AccessRequest
from routes import main_bp, admin_bp
from dotenv import load_dotenv
import os
import msal
from flask_migrate import Migrate

# Load environment variables from .env file
load_dotenv()

print("SECRET_KEY:", os.getenv('SECRET_KEY'))
print("DATABASE_URL:", os.getenv('DATABASE_URL'))
print("CLIENT_ID:", os.getenv('CLIENT_ID'))
print("CLIENT_SECRET:", os.getenv('CLIENT_SECRET'))
print("AUTHORITY:", os.getenv('AUTHORITY'))
print("REDIRECT_PATH:", os.getenv('REDIRECT_PATH'))

def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)
    migrate = Migrate(app, db)

    with app.app_context():
        db.create_all()

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    @app.route("/login")
    def login():
        session["flow"] = _build_auth_code_flow(scopes=app.config["SCOPE"])
        return redirect(session["flow"]["auth_uri"])

    @app.route(app.config["REDIRECT_PATH"])
    def authorized():
        try:
            cache = _load_cache()
            result = _build_msal_app(cache=cache).acquire_token_by_auth_code_flow(session.get("flow", {}), request.args)
            if "error" in result:
                return render_template("auth_error.html", result=result)
            session["user"] = result.get("id_token_claims")
            _save_cache(cache)
        except ValueError:  # Usually caused by CSRF
            pass  # Simply ignore them
        return redirect(url_for("index"))

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(
            app.config["AUTHORITY"] + "/oauth2/v2.0/logout" +
            "?post_logout_redirect_uri=" + url_for("index", _external=True))

    return app

def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        Config.CLIENT_ID, authority=authority or Config.AUTHORITY,
        client_credential=Config.CLIENT_SECRET, token_cache=cache)

def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()

def _build_auth_code_flow(scopes=None, authority=None):
    return _build_msal_app(authority=authority).initiate_auth_code_flow(
        scopes or [],
        redirect_uri=url_for("authorized", _external=True))

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)