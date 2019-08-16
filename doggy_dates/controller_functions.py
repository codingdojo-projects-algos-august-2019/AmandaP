from flask import render_template, request, redirect, session, url_for, flash, jsonify
from models.user_models import User, users_schema, user_schema
from models.event_models import Event, event_schema, events_schema, EventAttendance, EventSizeRestriction,\
    EventViewed, EventMessage
from models.dog_models import Dog, dogs_schema, dog_schema
from dateutil.parser import parse
from config import db, app
from datetime import datetime
from werkzeug.utils import secure_filename
import os, requests, json

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
sizes = [
    {'id': 1, 'category': 'x-small', 'selected': False},
    {'id': 2, 'category': 'small', 'selected': False},
    {'id': 3, 'category': 'medium', 'selected': False},
    {'id': 4, 'category': 'large', 'selected': False},
    {'id': 5, 'category': 'x-large', 'selected': False},
]

def page_not_found(e):
  return render_template('404.html'), 404

app.register_error_handler(404, page_not_found)

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
    if 'userid' not in session:
        return redirect('/')
    user_obj = User.query.get(session['userid'])
    dogs = dogs_schema.dump(user_obj.user_dogs)
    session['user_dogs'] = dogs.data
    new_messages = 0
    for event in user_obj.user_events:
        new_messages = check_new_messages(event.event_details)
        event.event_details.upcoming = check_upcoming(event.event_details)
    for event in user_obj.hosted_events:
        new_messages = new_messages + check_new_messages(event)
        event.upcoming = check_upcoming(event)
    return render_template('index.html', user=user_obj, new_messages=new_messages)


# creating functions

def create_event():
    if 'userid' not in session:
        return redirect('/')
    if request.method == 'GET':
        if len(session['user_dogs']) == 0:
            flash('must have dog to create event', 'error')
            return redirect('/')
        return render_template('create_event.html')
    time = request.form['date'] + ' ' + request.form['time']
    data = {
        'size_restrictions': request.form.getlist('size_restrictions[]'),
        'event_time': time
    }
    validated_event = Event.validate_event(data)
    if validated_event:
        event = event_schema.dump(request.form)
        event.data['event_time'] = time
        event.data['creator_id'] = session['userid']
        new_event = Event.add_event(event.data)
        conflicts = get_conflicts(new_event)
        if len(conflicts) > 0:
            for conflict in conflicts:
                conflicting_event = EventAttendance.leave_event(conflict)
                flash('You have been removed from {} due to time_conflict'.format(conflicting_event), 'warning')
        if new_event:
            for restriction in request.form.getlist('size_restrictions[]'):
                EventSizeRestriction.add_restriction(data={'event': new_event.id, 'size_id': restriction})
        flash('Event successfully added', 'success')
        return redirect('/alerts')
    return redirect('/alerts')

def create_dog():
    if 'userid' not in session:
        return redirect('/')
    if request.method == 'GET':
        return render_template('create_dog.html')
    dog = dog_schema.dump(request.form)
    dog.data['owner_id'] = session['userid']
    new_dog = Dog.add_dog(dog.data)
    if new_dog:
        dog = dog_schema.dump(new_dog)
        session['user_dogs'].append(dog)
        user = User.query.get(session['userid'])
        flash('Dog successfully added', 'success')
        for event in user.user_events:
            attending = True
            for restricted in event.event_details.size_restrictions:
                if restricted.id == new_dog.size:
                    attending = False
            if not attending:
                event_name = EventAttendance.leave_event(event.event_details.id)
                flash('You were removed from event {} due to weight restrictions'.format(event_name), 'warning')
        for event in user.hosted_events:
            for restricted in event.size_restrictions:
                if restricted.id == new_dog.size:
                    flash('Removing restriction from this event', 'warning')
                    EventSizeRestriction.remove_restriction(data={'event' : event.id, 'size_id': restricted.id})
    return redirect('/')


def create_message(id):
    if 'userid' not in session:
        return redirect('/')
    data = {
        'event_id': id,
        'text': request.form['text'],
        'poster_id': int(session['userid'])
    }
    new_message = EventMessage.validate_message(data)
    if new_message:
        EventMessage.add_message(data)
        flash('Message added', 'success')
    return redirect('/events/{}'.format(id))


# viewing functions

def show_event(id, weather=None):
    if 'userid' not in session:
        return redirect('/')
    event_viewed = EventViewed(event_id=id, viewer_id=session['userid'])
    db.session.add(event_viewed)
    db.session.commit()
    event = Event.query.get(id)
    attendance = check_attendance(event)
    event.upcoming = check_upcoming(event)
    event.user_restrictions = []
    user = User.query.get(session['userid'])
    days_until = check_days_until(event)
    if days_until < 7:
        weather_data = check_event_weather(event.zip_code, event.event_time)
        weather = weather_data['dailyForecasts']['forecastLocation']['forecast'][days_until - 1]['iconLink']
    if event.creator_id != session['userid']:
        event.time_conflict = check_hosting_time_conflict(event, get_user_events(session['userid']))
    if user not in event.attendees:
            if check_size_restrictions(event):
                event.user_restrictions.append('Size Restriction')
            if check_capacity(event.capacity, attendance):
                event.user_restrictions.append('Too many dogs')
            if check_attending_time_conflict(event, get_user_events(session['userid'])):
                event.user_restrictions.append('Time Conflict')
    return render_template('event_details.html', event=event, edit=False, weather=weather)


def show_events():
    if 'userid' not in session:
        return redirect('/')
    events = Event.query.all()
    user = User.query.get(session['userid'])
    user_events = get_user_events(user.id)
    for event in events:
        #is the event upcoming
        event.upcoming = check_upcoming(event)
        #use this to build a list of user restrictions instead of setting each to a true false
        event.user_restrictions = []
        # get number of dogs in attendance for event
        attendance = check_attendance(event)
        # if this is not the users event check for conflicts
        if event.creator_id != session['userid']:
            if check_hosting_time_conflict(event, user_events):
                event.user_restrictions.append('Time Conflict')
        # if user is not in attendance already (which means they should have been fine to join or has not been removed
        # then check for time conflicts, space conflicts, size conflicts
        if user not in event.attendees:
            if check_size_restrictions(event):
                event.user_restrictions.append('Size Restriction')
            if check_capacity(event.capacity, attendance):
                event.user_restrictions.append('Too many dogs')
            if check_attending_time_conflict(event, user_events):
                event.user_restrictions.append('Time Conflict')
    return render_template('events.html', events=events)


def show_updated_events():
    if 'userid' not in session:
        return redirect('/')
    events = Event.query.all()
    user = User.query.get(session['userid'])
    user_events = get_user_events(user.id)
    if request.method == 'POST':
        text = request.form['search_text']
        if request.form['search_term'] == 'name':
            events = Event.query.filter(Event.name.like("%{}%".format(text))).all()
    for event in events:
        #is the event upcoming
        event.upcoming = check_upcoming(event)
        #use this to build a list of user restrictions instead of setting each to a true false
        event.user_restrictions = []
        # get number of dogs in attendance for event
        attendance = check_attendance(event)
        # if this is not the users event check for conflicts
        if event.creator_id != session['userid']:
            if check_hosting_time_conflict(event, user_events):
                event.user_restrictions.append('Time Conflict')
        # if user is not in attendance already (which means they should have been fine to join or has not been removed
        # then check for time conflicts, space conflicts, size conflicts
        if user not in event.attendees:
            if check_size_restrictions(event):
                event.user_restrictions.append('Size Restriction')
            if check_capacity(event.capacity, attendance):
                event.user_restrictions.append('Too many dogs')
            if check_attending_time_conflict(event, user_events):
                event.user_restrictions.append('Time Conflict')
    return render_template('event_partials.html', events=events)

def show_users_dogs(id):
    if 'userid' not in session:
        return redirect('/')
    owner_page = False
    owner = User.query.get(id)
    dogs = Dog.query.filter_by(owner_id=id).all()
    if int(id) == session['userid']:
        owner_page = True
    return render_template('dogs.html', dogs=dogs, owner=owner, owner_page=owner_page)


def show_dog(id):
    if 'userid' not in session:
        return redirect('/')
    dog = Dog.query.get(id)
    return render_template('dog_profile.html', dog=dog)

def show_user(id):
    if 'userid' not in session:
        return redirect('/')
    user = User.query.get(id)
    for event in user.user_events:
        event.upcoming = check_upcoming(event.event_details)
    for event in user.hosted_events:
        event.upcoming = check_upcoming(event)
    return render_template('user_profile.html', user=user)

# editing functions

def edit_event(id, size_restrictions=None):
    if 'userid' not in session:
        return redirect('/')
    event = Event.query.get(id)
    if event.creator_id != session['userid']:
        flash('You cannot edit this event', 'error')
        return redirect('/events/{}'.format(id))
    if check_days_until(event) < 1:
        flash('Cannot edit events happening within 24 hours', 'error')
        return redirect('/')
    if request.method == 'GET':
        restrictions = []
        for size in event.size_restrictions:
            restrictions.append(size.id)
        return render_template('event_details.html', edit=True, event=event, restrictions=restrictions)
    time = request.form['date'] + ' ' + request.form['time']
    if len(event.attendees) == 0:
        size_restrictions = request.form.getlist('size_restrictions[]')
    data = {
        'id': id,
        'size_restrictions': size_restrictions,
        'event_time' : time
    }
    validated_event = Event.validate_existing_event(data)
    if validated_event:
        event.name = request.form['name']
        event.address = request.form['address']
        event.city = request.form['city']
        event.state = request.form['state']
        event.zip_code = request.form['zip_code']
        event.event_time = parse_date("{} {}".format(request.form['date'], request.form['time']))
        if len(event.attendees) == 0:
            event.capacity = request.form['capacity']
            EventSizeRestriction.query.filter_by(event_id=id).delete()
            db.session.commit()
            for restriction in request.form.getlist('size_restrictions[]'):
                add_restriction = EventSizeRestriction(event_id=id, size_id=restriction)
                db.session.add(add_restriction)
                db.session.commit()
        conflicts = get_conflicts(event)
        if len(conflicts) > 0:
            for conflict in conflicts:
                conflicting_event = EventAttendance.leave_event(conflict)
                flash('You have been removed from {} due to time conflict'.format(conflicting_event),
                      'warning')
        flash('Event updated', 'success')
        return redirect('/events/{}'.format(id))
    return redirect('/events/{}/edit'.format(id))


def edit_dog(id):
    if 'userid' not in session:
        return redirect('/')
    dog = Dog.query.get(id)
    if dog.owner_id != session['userid']:
        flash('You cannot edit this dog', 'error')
        return redirect('/')
    return render_template('dog_profile.html', dog=dog, edit=True)


def edit_user(id):
    if 'userid' not in session:
        return redirect('/')
    return render_template('event.html', event=event)


# deleting functions

def delete_event(id):
    if 'userid' not in session:
        return redirect('/')
    event = Event.query.get(id)
    if not check_upcoming(event):
        flash('You cannot delete past event', 'error')
        return redirect('/')
    if check_days_until(event) < 1:
        flash('Cannot delete events happening within 24 hours', 'error')
    if event.creator_id != session['userid']:
        flash('You cannot edit this event', 'error')
        return redirect('/events/{}'.format(id))
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted', 'success')
    return redirect('/')


def delete_dog(id):
    if 'userid' not in session:
        return redirect('/')
    dog = Dog.query.get(id)
    if dog.owner_id != session['userid']:
        flash('You cannot delete this dog', 'error')
        return redirect('/')
    if dog.profile_picture:
        delete_file = secure_filename(dog.profile_picture)
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], delete_file))
    db.session.delete(dog)
    db.session.commit()
    flash('Dog successfully deleted', 'info')
    return redirect('/')


def delete_user(id):
    if 'userid' not in session:
        return redirect('/')
    user = User.query.get(id)
    if user.id == session['userid']:
        flash('You cannot delete while logged in', 'error')
        return redirect('/')
    db.session.delete(user)
    db.session.commit()
    flash('User successfully deleted', 'info')
    return redirect('/')

def delete_message(id):
    if 'userid' not in session:
        return redirect('/')
    msg = EventMessage.query.get(id)
    if msg.poster_id != session['userid']:
        flash('You cannot delete this message', 'error')
        return redirect('/')
    db.session.delete(msg)
    db.session.commit()
    return redirect('/')

# joining and leaving events
def join_event(id):
    if request.method == 'GET' or 'userid' not in session:
        return redirect('/')
    event = Event.query.get(id)
    if not check_upcoming(event):
        flash('You cannot join past event', 'error')
        return redirect('/alerts')
    if event.creator_id == session['userid']:
        flash('You cannot join your own event', 'error')
        return redirect('/alerts')
    if check_if_attending(id):
        flash('You have already joined this event', 'warning')
        return redirect('/alerts')
    if check_capacity(event.capacity,check_attendance(event)):
        flash('Cannot join due to capacity', 'error')
        return redirect('/alerts')
    user_events = get_user_events(session['userid'])
    if check_size_restrictions(event):
        flash('Cannot join due to size restrictions', 'error')
        return redirect('/alerts')
    if check_hosting_time_conflict(event, user_events):
        flash('You are hosting an event at this time', 'error')
        return redirect('/alerts')
    if check_attending_time_conflict(event, user_events):
        flash('You are attending an event at this time', 'error')
        return redirect('/alerts')
    EventAttendance.join_event(id)
    return redirect('/alerts')


def leave_event(id):
    if request.method == 'GET' or 'userid' not in session:
        flash('Leave request error', 'error')
        return redirect('/')
    event = Event.query.get(id)
    if not check_upcoming(event):
        flash('You cannot leave past event', 'error')
        return redirect('/alerts')
    if not check_if_attending(id):
        flash('You were not attending this event', 'warning')
        return redirect('/alerts')
    EventAttendance.leave_event(id)
    return redirect('/alerts')

# extra functions

def check_if_attending(id):
    already_attending = False
    event_attendance = EventAttendance.query.filter_by(event_id=id, user_id = session['userid']).first()
    if event_attendance is not None:
        already_attending = True
    return already_attending

def check_hosting_time_conflict(new_event, user_events):
    time_conflict = False
    for event in user_events['hosted_events']:
        if new_event.event_time == event.event_time:
            time_conflict = True
    return time_conflict

def check_attending_time_conflict(new_event, user_events):
    time_conflict = False
    for event in user_events['user_events']:
        if new_event.event_time == event.event_details.event_time:
            time_conflict = True
    return time_conflict

def check_attendance(event):
    event.attending = 0
    for owner in event.attendees:
        event.attending =+ len(owner.user_dogs)
        if session['userid'] == owner.id:
            event.session_user_attending=True
    return event.attending

def check_capacity(capacity, attendance):
    capacity_full = False
    if int(attendance) + int(len(session['user_dogs'])) > int(capacity):
        capacity_full = True
    return capacity_full

def check_new_messages(event):
    new_messages = 0
    get_last_view = EventViewed.query.filter_by(event_id=event.id, viewer_id=session['userid']).all()
    if get_last_view:
        viewed_event = get_last_view.pop()
        for message in event.event_messages:
                if message.created_at > viewed_event.created_at:
                    event.has_new_message = True
                    new_messages = new_messages + 1
    return new_messages

def check_size_restrictions(event):
    size_restriction = False
    for restriction in event.size_restrictions:
        for dog in session['user_dogs']:
            if int(dog['size']) == restriction.id:
                size_restriction = True
    return size_restriction


def check_event_weather(zip_code, date):
    url = 'https://weather.api.here.com/weather/1.0/report.json?' \
          'app_id=hTbK4O9DbrxVabKcFg9C&app_code=xd7WMhnk_GKoFfLViHyntA&' \
          'product=forecast_7days_simple&zipcode={}&hourlydate={}'\
        .format(zip_code, date.strftime('%Y-%m-%d'))
    response = requests.get(url = url).json()
    return response

def check_upcoming(event):
    upcoming = True
    if datetime.now() > event.event_time:
        upcoming = False
    return upcoming

def check_days_until(event):
    time = event.event_time - datetime.now()
    return time.days

def get_conflicts(new_event):
    conflicts = []
    users_events = get_user_events(session['userid'])
    for event in users_events['user_events']:
        if new_event.event_time == event.event_details.event_time:
            conflicts.append(event.event_details.id)
    return conflicts

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_file(id):
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        dog = Dog.query.get(id)
        if dog.profile_picture:
            delete_file = secure_filename(dog.profile_picture)
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], delete_file))
        filename = '{}_'.format(dog.id) + secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        dog.profile_picture = filename
        db.session.commit()
        return redirect('/dogs/{}'.format(id))


def alert():
    return render_template('alerts.html')

def parse_date(date_obj):
    return parse(date_obj)

def get_user_events(userid):
    user = User.query.get(userid)
    users_events = {
        'user_events': user.user_events,
        'hosted_events': user.hosted_events
    }
    return users_events