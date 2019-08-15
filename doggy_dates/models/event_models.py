from config import db, bcrypt
from sqlalchemy.sql import func
from flask import session, flash
from marshmallow import Schema, fields
from .user_models import UserSchema, User
from .dog_models import DogSchema, DogSize
from dateutil.parser import parse
from sqlalchemy.orm import relationship, backref
from datetime import datetime

def parse_date(date_obj):
    return parse(date_obj)

class Event(db.Model):
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45))
    description = db.Column(db.Text())
    capacity = db.Column(db.Text())
    address = db.Column(db.Text())
    city = db.Column(db.Text())
    state = db.Column(db.Text())
    zip_code = db.Column(db.Integer)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_time = db.Column(db.DateTime, server_default=func.now())
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    # relationships
    creator = db.relationship('User', foreign_keys=[creator_id], backref="hosted_events")
    attendees = db.relationship('User', secondary="attendees")
    size_restrictions = db.relationship('DogSize', secondary="size_restrictions")

    @classmethod
    def validate_event(cls, data):
        is_valid = True
        if datetime.now() > parse_date(data['event_time']):
            flash('Event must be for future date', 'error')
            is_valid = False
        user = User.query.get(session['userid'])
        for hosting in user.hosted_events:
            if hosting.id != int(data['id']):
                if hosting.event_time == parse_date(data['event_time']):
                    is_valid = False
                    flash('You have an event already scheduled for this time', 'error')
                    return is_valid
        for size in data['size_restrictions']:
            for dog in session['user_dogs']:
                if int(size) == int(dog['size']):
                    is_valid = False
                    flash('Cannot restrict dogs the same size as your own', 'error')
                    return is_valid
        return is_valid

    @classmethod
    def add_event(cls, data):
        data['event_time'] = parse_date(data['event_time'])
        new_event = Event(**data)
        db.session.add(new_event)
        db.session.commit()
        return new_event

class EventSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    description = fields.String()
    capacity = fields.Integer()
    creator_id = fields.Integer()
    event_time = fields.String()
    address = fields.String()
    city = fields.String()
    state = fields.String()
    zip_code = fields.Integer()


event_schema = EventSchema()
events_schema = EventSchema(many=True)


class EventAttendance(db.Model):
    __tablename__ = "attendees"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    event = db.relationship('Event', foreign_keys=[event_id], backref="event_details")
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=backref("user_events", cascade="all, delete-orphan"))

    @classmethod
    def leave_event(cls, data):
        attendance = EventAttendance.query.filter_by(event_id=data, user_id=session['userid']).first()
        db.session.delete(attendance)
        db.session.commit()
        flash('Event left', 'success')
        return

    @classmethod
    def join_event(cls, data):
        attendance = EventAttendance(event_id=data, user_id=session['userid'])
        db.session.add(attendance)
        db.session.commit()
        flash('Event joined', 'success')
        return

class EventSizeRestriction(db.Model):
    __tablename__ = "size_restrictions"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    size_id = db.Column(db.Integer, db.ForeignKey('dog_sizes.id'), nullable=False)
    size = db.relationship('DogSize', backref=backref("event_restrictions", cascade="all, delete-orphan"))


class EventMessage(db.Model):
    __tablename__ = "event_messages"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text())
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    event = db.relationship('Event', foreign_keys=[event_id], backref=backref("event_messages", cascade="all,delete"))
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    poster = db.relationship('User', foreign_keys=[poster_id])
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())


    @classmethod
    def validate_message(cls, data):
        is_valid = True
        if len(data['text']) < 1:
            flash('Text cannot be empty', 'error')
            is_valid = False
        return is_valid

    @classmethod
    def add_message(cls, data):
        new_msg = EventMessage(**data)
        db.session.add(new_msg)
        db.session.commit()
        return new_msg


class EventViewed(db.Model):
    __tablename__ = "event_views"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    viewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
