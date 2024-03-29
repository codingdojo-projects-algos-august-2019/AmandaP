from config import db, bcrypt
from sqlalchemy.sql import func
from flask import session, flash
import re
from marshmallow import Schema, fields
from datetime import datetime
email_validator = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
name_validator = re.compile(r'^[-a-zA-Z]+$')


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(45))
    last_name = db.Column(db.String(45))
    email = db.Column(db.String(45))
    password = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    @classmethod
    def validate_user(cls, data):
        is_valid = True
        if len(data['first_name']) > 1:
            if not name_validator.match(data['first_name']):
                is_valid = False
                flash('First name can only contain letters', 'error')
        else:
            is_valid = False
            flash('First Name is required', 'error')
        if len(data['last_name']) > 1:
            if not name_validator.match(data['last_name']):
                is_valid = False
                flash('Last name can only contain letters', 'error')
        else:
            is_valid = False
            flash('Last Name is required', 'error')
        if len(data['password']) > 1:
            if data['password'] != data['confirm_password']:
                is_valid = False
                flash('Passwords must match', 'error')
        else:
            is_valid = False
            flash('Password must not be blank', 'error')
        if len(data['email']) > 1:
            if not email_validator.match(data['email']):
                is_valid = False
                flash('Enter valid email address', 'error')
        else:
            is_valid = False
            flash('Email must not be blank', 'error')
        return is_valid

    @classmethod
    def email_taken(cls, data):
        is_valid = False
        message = 'Enter a valid email'
        if email_validator.match(data):
            is_valid = True
            email_check = User.query.filter(User.email.ilike("%{}%".format(data))).first()
            if email_check:
                is_valid = False
                message = 'Email already exists'
        return {'available': is_valid, 'message': message}

    @classmethod
    def register_user(cls, data):
        data['password'] = bcrypt.generate_password_hash(data['password'])
        new_user = User(**data)
        db.session.add(new_user)
        db.session.commit()
        return new_user

    @classmethod
    def validate_login_data(cls, data):
        is_valid = True
        if len(data['email']) < 1:
            is_valid = False
            flash('Email field blank', 'error')
        if not email_validator.match(data['email']):
            is_valid = False
            flash('Enter valid email address', 'error')
        if len(data['password']) < 1:
            is_valid = False
            flash('Password field blank', 'error')
        return is_valid

    @classmethod
    def login_user(cls, data):
        result = User.query.filter(User.email.ilike("%{}%".format(data['email']))).first()
        if result:
            active = ActiveUser.query.filter_by(user_id=result.id).first()
            if active is None:
                return False
            if bcrypt.check_password_hash(result.password, data['password']):
                # if we get True after checking the password, we may put the user id in session
                db.session.commit()
                return result
        return False

    @classmethod
    def update_user(cls, data):
        user = User.query.filter(id=data['id'])
        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.email = data['email']
        db.session.commit()
        return

class UserSchema(Schema):
    id = fields.Integer()
    first_name = fields.String()
    last_name = fields.String()
    email = fields.String()
    password = fields.String()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


user_schema = UserSchema()
users_schema = UserSchema(many=True, exclude=['password'])


class ActiveUser(db.Model):
    __tablename__ = "active_users"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    @classmethod
    def add_active(cls, data):
        added_user = ActiveUser(user_id=int(data), activated_by_id=session['userid'])
        db.session.add(added_user)
        db.session.commit()
        return

    @classmethod
    def deactivate_user(cls, data):
        user = ActiveUser.query.filter_by(user_id=int(data)).first()
        db.session.delete(user)
        db.session.commit()
        return

    @classmethod
    def validate_active(cls, data):
        active_status = ActiveUser.query.filter_by(user_id=data).first()
        if active_status is None:
            return False
        return True

