from flask import render_template, request, redirect, session, url_for, flash, jsonify
from models.user_models import User, users_schema, user_schema
from models.event_models import Event, event_schema, events_schema, EventAttendance, EventSizeRestriction
from models.dog_models import Dog, dogs_schema, dog_schema
from dateutil.parser import parse
from config import db, app
from datetime import datetime
from werkzeug.utils import secure_filename
import os

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

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
    if 'userid' not in session:
        return redirect('/')
    user_obj = User.query.get(session['userid'])
    dogs = dogs_schema.dump(user_obj.user_dogs)
    session['user_dogs'] = dogs.data
    for event in user_obj.user_events:
        if datetime.now() < event.event.event_time:
            event.upcoming = True
    return render_template('index.html', user=user_obj)


# creating functions

def create_event():
    if 'userid' not in session:
        return redirect('/')
    if request.method == 'GET':
        if len(session['user_dogs']) == 0:
            flash('must have dog to create event', 'error')
            return redirect('/')
        return render_template('create_event.html')
    data = {
        'size_restrictions': request.form.getlist('size_restrictions[]'),
        'event_time' : request.form['event_time']
    }
    validated_event = Event.validate_event(data)
    if validated_event:
        event = event_schema.dump(request.form)
        event.data['creator_id'] = session['userid']
        new_event = Event.add_event(event.data)
        if new_event:
            for restriction in request.form.getlist('size_restrictions[]'):
                add_restriction = EventSizeRestriction(event_id=new_event.id, size_id=restriction)
                db.session.add(add_restriction)
                db.session.commit()
        flash('Event successfully added', 'success')
        return redirect('/')
    return redirect('/events/create')

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
            for restricted in event.event.size_restrictions:
                if restricted.id == new_dog.size:
                    attending = False
                    flash('You were removed from event {} due to weight restrictions'.format(event.event.name), 'warning')
            if not attending:
                event_attendance = EventAttendance.query.filter_by(event_id = event.event.id, user_id = session['userid']).first()
                db.session.delete(event_attendance)
                db.session.commit()
        return redirect('/')
    return redirect('/')

# viewing functions

def show_event(id):
    if 'userid' not in session:
        return redirect('/')
    attending = 0
    event = Event.query.get(id)
    for owner in event.attendees:
        attending = attending + len(owner.user_dogs)
    return render_template('event_details.html', event=event, attending=attending, edit=False)

def show_events():
    print(datetime.now())
    if 'userid' not in session:
        return redirect('/')
    events = Event.query.all()
    for event in events:
        event.attending = 0
        for owner in event.attendees:
            if session['userid'] == owner.id:
                event.session_user_attending = True
            event.attending =+ len(owner.user_dogs)
    return render_template('events.html', events=events)

def show_search_events():
    attending = 0
    if 'userid' not in session:
        return redirect('/')
    events = []
    text = request.form['search_text']
    if request.form['search_term'] == 'name':
        events = Event.query.filter(Event.name.like("%{}%".format(text))).all()
    for event in events:
        for owner in event.attendees:
            if session['userid'] == owner.id:
                event.session_user_attending = True
            attending = attending + len(owner.user_dogs)
    return render_template('event_partials.html', events=events, attending=attending)

def show_users_dogs(id):
    if 'userid' not in session:
        return redirect('/')
    owner_page = False
    owner = User.query.get(id)
    dogs = Dog.query.filter_by(owner_id=id).all()
    if int(id) == session['userid']:
        owner_page = True
    return render_template('dogs.html', dogs=dogs, owner=owner, owner_page=owner_page)

def show_dog(dog_id):
    if 'userid' not in session:
        return redirect('/')
    dog = Dog.query.get(dog_id)
    return render_template('dog_profile.html', dog=dog)

def show_user(id):
    if 'userid' not in session:
        return redirect('/')
    return

# editing functions

def edit_event(id):
    if 'userid' not in session:
        return redirect('/')
    event = Event.query.get(id)
    if event.creator_id != session['userid']:
        flash('You cannot edit this event', 'error')
        return redirect('/events/{}'.format(id))
    if request.method == 'GET':
        sizes = [
            {'id': 1, 'category' : 'x-small', 'selected': False},
            {'id': 2, 'category' : 'small',  'selected': False},
            {'id': 3, 'category' : 'medium',  'selected': False},
            {'id': 4, 'category' : 'large',  'selected': False},
            {'id': 5, 'category' : 'x-large',  'selected': False},
        ]
        for restriction in event.size_restrictions:
            for size in sizes:
                if restriction.id == size['id']:
                    size['selected'] = True
        return render_template('event_details.html', edit=True, event=event, sizes=sizes)
    data = {
        'size_restrictions': request.form.getlist('size_restrictions[]'),
        'event_time' : request.form['event_time']
    }
    validated_event = Event.validate_event(data)
    if validated_event:
        event.name = request.form['name']
        event.address = request.form['address']
        event.city = request.form['city']
        event.state = request.form['state']
        event.zip_code = request.form['zip_code']
        event.event_time = parse_date(request.form['event_time'])
        event.capacity = request.form['capacity']
        EventSizeRestriction.query.filter_by(event_id=id).delete()
        db.session.commit()
        for restriction in request.form.getlist('size_restrictions[]'):
            add_restriction = EventSizeRestriction(event_id=id, size_id=restriction)
            db.session.add(add_restriction)
            db.session.commit()
        db.session.commit()
        return redirect('/events/{}'.format(id))
    return redirect('/events/{}/edit'.format(id))

def edit_dog(id):
    if 'userid' not in session:
        return redirect('/')
    return render_template('event.html', event=event)

def edit_user(id):
    if 'userid' not in session:
        return redirect('/')
    return render_template('event.html', event=event)

# deleting functions

def delete_event(id):
    if 'userid' not in session:
        return redirect('/')
    event = Event.query.get(id)
    if datetime.now() > event.event_time:
        flash('You cannot delete past event', 'error')
        return redirect('/')
    if event.creator_id != session['userid']:
        flash('You cannot edit this event', 'error')
        return redirect('/events/{}'.format(id))
    return
def delete_dog(id):
    if 'userid' not in session:
        return redirect('/')
    return
def delete_user(id):
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

# joining and leaving events

def join_event(id):
    if 'userid' not in session:
        return redirect('/')
    event = Event.query.get(id)
    if datetime.now() > event.event_time:
        flash('You cannot join past event', 'error')
        return redirect('/')
    if event.creator_id == session['userid']:
        flash('You cannot join your own event', 'error')
        return redirect('/')
    check_attendance = EventAttendance.query.filter_by(event_id=id, user_id = session['userid']).first()
    if check_attendance:
        flash('You have already joined this event', 'warning')
        return redirect('/')
    event_attendance = EventAttendance(event_id=id, user_id = session['userid'])
    db.session.add(event_attendance)
    db.session.commit()
    return redirect('/')

def leave_event(id):
    if 'userid' not in session:
        return redirect('/')
    event = Event.query.get(id)
    if datetime.now() > event.event_time:
        flash('You cannot leave past event', 'error')
        return redirect('/')
    check_attendance = EventAttendance.query.filter_by(event_id=id, user_id = session['userid']).first()
    if check_attendance is None:
        flash('You were not attending this event', 'warning')
        return redirect('/')
    event_attendance = EventAttendance.query.filter_by(event_id = id, user_id = session['userid']).first()
    db.session.delete(event_attendance)
    db.session.commit()
    return redirect('/')

# extra functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_file(dog_id):
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        dog = Dog.query.get(dog_id)
        if dog.profile_picture:
            delete_file = secure_filename(dog.profile_picture)
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], delete_file))
        filename = '{}_'.format(dog.id) + secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        dog.profile_picture = filename
        db.session.commit()
        return redirect('/dogs/{}'.format(dog_id))
