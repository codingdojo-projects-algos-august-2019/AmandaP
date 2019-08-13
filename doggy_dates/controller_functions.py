from flask import render_template, request, redirect, session, url_for, flash, jsonify
from models.user_models import User, users_schema, user_schema
from models.event_models import Event, event_schema, events_schema, EventAttendance
from models.dog_models import Dog, dogs_schema, dog_schema
from dateutil.parser import parse
from config import db


def parse_date(date_obj):
    return parse(date_obj)


def index():
    if 'userid' not in session:
        return render_template('login.html')
    return redirect('/dashboard')


def register():
    validated_data = User.validate_user(request.form)
    if validated_data:
        user = user_schema.dump(request.form)
        create_user = User.register_user(user.data)
        if create_user:
            flash('User successfully added', 'success')
            return redirect('/')
        flash('There has been an error', 'error')
    return redirect('/')


def login():
    validated_data = User.validate_login_data(request.form)
    if validated_data:
        user = user_schema.dump(request.form)
        result = User.login_user(user.data)
        if result:
            session['userid'] = result.id
            return redirect('/dashboard')
        flash('You could not be logged in', 'error')
    return redirect('/')


def logout():
    session.clear()
    return redirect('/')

def dashboard():
    user_obj = User.query.get(session['userid'])
    print(user_obj.events_user_is_attending)
    return render_template('index.html', user=user_obj)

# creating functions

def create_event():
    user = User.query.get(session['userid'])
    if len(user.user_dogs) == 0:
        flash('must have dog to create event', 'error')
        return redirect('/')
    event = event_schema.dump(request.form)
    event.data['creator_id'] = session['userid']
    new_event = Event.add_event(event.data)
    if new_event:
        flash('Event successfully added', 'success')
        return redirect('/')


def create_dog(id):
    print(request.form)
    dog = dog_schema.dump(request.form)
    dog.data['owner_id'] = session['userid']
    new_dog = Dog.add_dog(dog.data)
    if new_dog:
        flash('Dog successfully added', 'success')
        return redirect('/')
    flash('There has been an error', 'error')
    return redirect('/')

# viewing functions

def show_event(id):
    event = Event.query.get(id)
    dog_attendees = []
    large_dogs = False
    small_dogs = False
    spots_remaining = event.event_capacity - len(event.creator.user_dogs)
    for dog in event.creator.user_dogs:
        dog_attendees.append(dog)
    attendees = EventAttendance.query.filter_by(event_id = id).all()
    for attendee in attendees:
        for dog in attendee.user.user_dogs:
            dog_attendees.append(dog)
            spots_remaining = spots_remaining - 1
    for dog in dog_attendees:
        if dog.owner.id != event.creator.id:
            if dog.weight >= 75:
                large_dogs = True
            elif dog.weight <= 20:
                small_dogs = True
    print(small_dogs, large_dogs)
    return render_template('events.html', event=event, dog_attendees = dog_attendees, spots_remaining = spots_remaining, large=large_dogs, small=small_dogs)

def show_events():
    events = Event.query.all()
    dog_attendees = []
    for event in events:
        print(event.id)
        event_attendances = EventAttendance.query.filter_by(event_id = event.id).all()
        for attendees in event_attendances:
            for dogs in attendees.user.user_dogs:
                dog_attendees.append(dogs)
    print(dog_attendees)
    return render_template('events.html', events=events)

def show_users_dogs(id):
    owner_page = False
    owner = User.query.get(id)
    dogs = Dog.query.filter_by(owner_id=id).all()
    if int(id) == session['userid']:
        owner_page = True
    return render_template('dogs.html', dogs=dogs, owner=owner, owner_page=owner_page)

def show_dog(id):
    return render_template('events.html', event=event)

def show_user(id):
    return

# editing functions

def edit_event(id):
    return render_template('event.html', event=event)

def edit_dog(id):
    return render_template('event.html', event=event)

def edit_user(id):
    return render_template('event.html', event=event)

# deleting functions

def delete_event(id):
    return
def delete_dog(id):
    return
def delete_user(id):
    return