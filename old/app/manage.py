import os
from dotenv import load_dotenv
load_dotenv()

from app import create_app
from models import db
from flask_migrate import Migrate

app = create_app()
migrate = Migrate(app, db)

@app.cli.command()
def deploy():
    """Run deployment tasks."""
    from flask_migrate import upgrade
    upgrade()

if __name__ == "__main__":
    app.run(host='localhost', port=5000)