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


def get_event_time(date, time):
    return parse_date("{} {}".format(date, time))


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
        if datetime.now() > get_event_time(data['date'], data['time']):
            flash('Event must be for future date', 'error')
            is_valid = False
        user = User.query.get(session['userid'])
        for hosting in user.hosted_events:
            if hosting.event_time == get_event_time(data['date'], data['time']):
                is_valid = False
                flash('You have an event already scheduled for this time', 'error')
        dog_sizes = []
        for dog in user.user_dogs:
            dog_sizes.append(dog.size)
        for size in data['size_restrictions']:
            if int(size) in dog_sizes:
                is_valid = False
                flash('Cannot restrict dogs the same size as your own', 'error')
                return is_valid
        return is_valid

    @classmethod
    def validate_existing_event(cls, data):
        is_valid = True
        if datetime.now() > get_event_time(data['date'], data['time']):
            flash('Event must be for future date', 'error')
            is_valid = False
        user = User.query.get(session['userid'])
        for hosting in user.hosted_events:
            if hosting.id != int(data['id']):
                if hosting.event_time == get_event_time(data['date'], data['time']):
                    is_valid = False
                    flash('You have an event already scheduled for this time', 'error')
                    return is_valid
        if data['size_restrictions']:
            dog_sizes = []
            user = User.query.get(session['userid'])
            for dog in user.user_dogs:
                dog_sizes.append(dog.size)
            for size in data['size_restrictions']:
                if int(size) in dog_sizes:
                    is_valid = False
                    flash('Cannot restrict dogs the same size as your own', 'error')
                    return is_valid
        return is_valid

    @classmethod
    def edit_event(cls, data):
        event = Event.query.get(data['id'])
        event.name = data['name']
        event.address = data['address']
        event.city = data['city']
        event.state = data['state']
        event.zip_code = data['zip_code']
        event.capacity = data['capacity']
        event.event_time = get_event_time(data['date'], data['time'])

    @classmethod
    def add_event(cls, data):
        event_data = add_event_schema.dump(data)
        event_data.data['event_time'] = get_event_time(data['date'], data['time'])
        new_event = Event(**event_data.data)
        db.session.add(new_event)
        db.session.commit()
        return new_event


class EventSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    description = fields.String()
    capacity = fields.Integer()
    creator_id = fields.Integer()
    event_time = fields.String(required=False)
    date = fields.String(required=False)
    time = fields.String(required=False)
    size_restrictions = fields.List(fields.Nested('EventSizeRestriction'), required=False)
    address = fields.String()
    city = fields.String()
    state = fields.String()
    zip_code = fields.Integer()


event_schema = EventSchema()
add_event_schema = EventSchema(exclude=['time', 'date'])
events_schema = EventSchema(many=True)


class EventAttendance(db.Model):
    __tablename__ = "attendees"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    event_details = db.relationship('Event', foreign_keys=[event_id], backref=backref("event_details", cascade="all, delete-orphan"))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=backref("user_events", cascade="all, delete-orphan"))

    @classmethod
    def leave_event(cls, data):
        attendance = EventAttendance.query.filter_by(event_id=data, user_id=session['userid']).first()
        event_name = attendance.event_details.name
        db.session.delete(attendance)
        db.session.commit()
        return event_name

    @classmethod
    def join_event(cls, data):
        attendance = EventAttendance(event_id=data, user_id=session['userid'])
        db.session.add(attendance)
        db.session.commit()
        return


class EventSizeRestriction(db.Model):
    __tablename__ = "size_restrictions"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    size_id = db.Column(db.Integer, db.ForeignKey('dog_sizes.id'), nullable=False)
    size = db.relationship('DogSize', backref=backref("event_restrictions", cascade="all, delete-orphan"))

    @classmethod
    def add_restriction(cls, data):
        restriction = EventSizeRestriction(event_id=data['event_id'], size_id=data['restriction'])
        db.session.add(restriction)
        db.session.commit()
        return restriction

    @classmethod
    def remove_restriction(cls, data):
        restriction = EventSizeRestriction.query.filter_by(event_id=data['event'], size_id=data['size_id']).first()
        db.session.delete(restriction)
        db.session.commit()
        return


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

    @classmethod
    def add_view(cls, data):
        view = EventViewed(event_id=data, viewer_id=session['userid'])
        db.session.add(view)
        db.session.commit()
        return

    @classmethod
    def update_view(cls, data):
        view = EventViewed.query.filter_by(event_id=data, viewer_id=session['userid']).first()
        view.updated_at = func.now()
        db.session.commit()
        return
