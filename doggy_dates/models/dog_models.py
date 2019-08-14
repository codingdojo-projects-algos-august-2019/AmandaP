from config import db, bcrypt
from sqlalchemy.sql import func
from flask import session, flash
from marshmallow import Schema, fields
from .user_models import UserSchema
from dateutil.parser import parse
from datetime import datetime

def parse_date(date_obj):
    return parse(date_obj)


class Dog(db.Model):
    __tablename__ = "dogs"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45))
    description = db.Column(db.Text)
    birthday = db.Column(db.DateTime)
    size = db.Column(db.Integer)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    profile_picture = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    #relationships
    owner = db.relationship('User', foreign_keys=[owner_id], backref="user_dogs")

    @classmethod
    def add_dog(cls, data):
        if datetime.now() < parse_date(data['birthday']):
            flash('Birthday must be in past', 'error')
            return False
        data['birthday'] = parse_date(data['birthday'])
        new_dog = Dog(**data)
        db.session.add(new_dog)
        db.session.commit()
        return new_dog

class DogSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    birthday = fields.String()
    description = fields.String()
    size = fields.Integer()
    owner_id = fields.Integer()
    """ here you would add any schemas of keys 
    messages = fields.Nested('MessageSchema', many=True)
    -- On whatever you are nesting if this Schema is part of that Schema
    you need to use exclude=['messages']
    """

dog_schema = DogSchema()
dogs_schema = DogSchema(many=True)

class DogSize(db.Model):
    __tablename__ = "dog_sizes"
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())