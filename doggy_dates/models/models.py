from config import db, bcrypt
from sqlalchemy.sql import func
from flask import session, flash
from marshmallow import Schema, fields


class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text())
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

class MessageSchema(Schema):
    id = fields.Integer()
    text = fields.String()

message_schema = MessageSchema()
messages_schema = MessageSchema(many=True)