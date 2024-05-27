from app import create_app
from models import db
from flask_migrate import Migrate, upgrade

app = create_app()
migrate = Migrate(app, db)

@app.cli.command()
def deploy():
    """Run deployment tasks."""
    # Migrate database to latest revision
    upgrade()

if __name__ == "__main__":
    app.run()