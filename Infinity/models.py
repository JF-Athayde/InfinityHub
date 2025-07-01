from Infinity import database, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(database.Model, UserMixin):
    id = database.Column(database.Integer, primary_key=True)
    username = database.Column(database.String(80), nullable=False)
    email = database.Column(database.String(120), unique=True, nullable=False)
    password_hash = database.Column(database.String(128), nullable=False)
    cargo = database.Column(database.String(50))
    bio = database.Column(database.Text)
    photo_url = database.Column(database.String(255), )

class Calendar(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    user_id = database.Column(database.Integer, database.ForeignKey('user.id'), nullable=False)
    user = database.relationship('User', backref='calendars')
    data = database.Column(database.DateTime, nullable=False, default=datetime.utcnow)
    title = database.Column(database.String(100), nullable=False)
    description = database.Column(database.Text)
    category = database.Column(database.String(50), nullable=False)
    warning = database.Column(database.Boolean, nullable=False)