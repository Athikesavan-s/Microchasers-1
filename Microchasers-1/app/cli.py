from flask.cli import with_appcontext
import click
from app import db
from app.models import User, Sample, Image, Detection

@click.command('clear-db')
@with_appcontext
def clear_db_command():
    """Clear all data from database."""
    db.session.query(Detection).delete()
    db.session.query(Image).delete()
    db.session.query(Sample).delete()
    db.session.query(User).delete()
    db.session.commit()
    click.echo('Cleared all database data.')