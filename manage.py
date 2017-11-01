from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from app.models import db
from app import app
migrate = Migrate(app, db)

# Creating instance of Manager class that handles commands
manager = Manager(app)

# Define migration command to always be preceded by the word "db" i.e python manage.py db migrate
manager.add_command('db', MigrateCommand)

if __name__ == "__main__":
    manager.run()