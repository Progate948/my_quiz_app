from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.types import JSON 

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)    
    answers = db.relationship('UserAnswer', backref='user', lazy='dynamic')
    checks = db.relationship('UserCheck', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Question(db.Model):
    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(JSON, nullable=False)
    correct_answer = db.Column(JSON, nullable=False)
    explanation = db.Column(db.Text, nullable=True)
    image_filename = db.Column(db.String(255), nullable=True)
    user_answers = db.relationship(
        'UserAnswer', 
        backref='question_detail', 
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    user_checks = db.relationship(
        'UserCheck', 
        backref='question_detail', 
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Question {self.id}>'

class UserAnswer(db.Model):
    __tablename__ = 'user_answer'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    user_selected_option = db.Column(JSON, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<UserAnswer {self.id} (User:{self.user_id}, Q:{self.question_id}, Correct:{self.is_correct})>'

class UserCheck(db.Model):
    __tablename__ = 'user_check'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    check_type = db.Column(db.String(50), nullable=False)
    is_checked = db.Column(db.Boolean, default=True, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'question_id', 'check_type', name='_user_question_check_uc'),)

    def __repr__(self):
        return f'<UserCheck {self.id} (User:{self.user_id}, Q:{self.question_id}, Type:{self.check_type}, Checked:{self.is_checked})>'