from config import db, bcrypt
from sqlalchemy.sql import func
from flask import session, flash
from marshmallow import Schema, fields
from .user_models import UserSchema
from .dog_models import DogSchema
from dateutil.parser import parse


def parse_date(date_obj):
    return parse(date_obj)

class Event(db.Model):
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45))
    description = db.Column(db.Text())
    event_capacity = db.Column(db.Integer)
    address = db.Column(db.Text())
    city = db.Column(db.Text())
    state = db.Column(db.Text())
    zip_code = db.Column(db.Integer)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    creator = db.relationship('User', foreign_keys=[creator_id], backref="hosted_events")
    event_time = db.Column(db.DateTime, server_default=func.now())
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())


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
    event_capacity = fields.Integer()
    creator_id = fields.Integer()
    event_time = fields.String()
    address = fields.String()
    city = fields.String()
    state = fields.String()
    zip_code = fields.Integer()


event_schema = EventSchema()
events_schema = EventSchema(many=True)


class EventAttendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    event = db.relationship('Event', foreign_keys=[event_id], backref="event_details")
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', foreign_keys=[user_id], backref="events_user_is_attending")