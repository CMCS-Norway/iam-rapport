from flask import Flask, redirect, url_for, session, request, render_template
from dotenv import load_dotenv
import os
import msal
from flask_migrate import Migrate
from flask_session import Session

# Load environment variables from .env file
load_dotenv()

# Import Config after loading environment variables
from config import Config
from models import db, User, Customer, AccessRequest
from routes import main_bp, admin_bp

def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    # Initialize Flask-Session
    app.config['SESSION_TYPE'] = 'filesystem'
    Session(app)

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
                print("Error in result:", result)
                return render_template("auth_error.html", result=result)
            session["user"] = result.get("id_token_claims")
            _save_cache(cache)
            
            # Log the token claims to ensure first and last name are available
            print("Token claims:", session["user"])

            # Check if the user is in one of the required groups
            user_groups = session["user"].get('groups', [])
            print("User Groups:", user_groups)
            print("Required Groups:", Config.REQUIRED_GROUPS)

            if not set(Config.REQUIRED_GROUPS).intersection(user_groups):
                print("User not in required groups")
                return render_template("auth_error.html", result={"error": "User not in required groups"})

            # Check if user is in admin group and store in session
            session["is_admin"] = Config.ADMIN_GROUP_ID in user_groups

            print("Redirecting to main.index")
            return redirect(url_for("main.index"))
        
        except ValueError as e:  # Usually caused by CSRF
            print("ValueError:", e)
            pass  # Simply ignore them

        print("Redirecting to main.index due to exception")
        return redirect(url_for("main.index"))

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(
            app.config["AUTHORITY"] + "/oauth2/v2.0/logout" +
            "?post_logout_redirect_uri=" + url_for("main.index", _external=True))

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
    app.run(host='localhost', port=5000, debug=False)