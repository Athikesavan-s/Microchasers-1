from .database import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    samples = db.relationship('Sample', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    readings = db.relationship('SensorReading', backref='sample', lazy='dynamic')
    images = db.relationship('Image', backref='sample', lazy='dynamic')

    def __repr__(self):
        return f'<Sample {self.name}>'

class SensorReading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Float)
    ph = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    sample_id = db.Column(db.Integer, db.ForeignKey('sample.id'))

    def __repr__(self):
        return f'<SensorReading {self.id}>'

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filepath = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    sample_id = db.Column(db.Integer, db.ForeignKey('sample.id'))
    detections = db.relationship('Detection', backref='image', lazy='dynamic')

    def __repr__(self):
        return f'<Image {self.filepath}>'

class Detection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    x_coordinate = db.Column(db.Integer, nullable=True)
    y_coordinate = db.Column(db.Integer, nullable=True)
    size = db.Column(db.Float, nullable=True)
    shape = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(7), nullable=True)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return f'<Detection {self.id} at ({self.x_coordinate}, {self.y_coordinate})>'
