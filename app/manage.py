from app import create_app
from models import db
from dotenv import load_dotenv
from flask_migrate import Migrate

# Load environment variables from .env file
load_dotenv()

app = create_app()
migrate = Migrate(app, db)

@app.cli.command()
def deploy():
    """Run deployment tasks."""
    from flask_migrate import upgrade
    upgrade()

if __name__ == "__main__":
    app.run()