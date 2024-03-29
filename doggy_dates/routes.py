from config import app
from controller_functions import index, register, login, logout, dashboard, show_user, show_users, show_dog,\
    show_event, show_events, join_event, leave_event, show_updated_events, edit_dog_picture, create_message, \
    delete_message, create_dog, create_event, edit_dog, edit_event, edit_user, delete_dog, delete_event,\
    delete_user, alert, activate_user, show_users_dogs, check_email

app.add_url_rule('/', view_func=index)
app.add_url_rule('/register', view_func=register, methods=['POST'])
app.add_url_rule('/login', view_func=login, methods=['POST'])
app.add_url_rule('/logout', view_func=logout)
app.add_url_rule('/dashboard', view_func=dashboard)
app.add_url_rule('/email', view_func=check_email, methods=['POST'])
app.add_url_rule('/alerts', view_func=alert)
app.add_url_rule('/events', view_func=show_events)
app.add_url_rule('/events/update', view_func=show_updated_events, methods=['GET','POST'])
app.add_url_rule('/events/create', view_func=create_event, methods=['GET','POST'])
app.add_url_rule('/events/<id>', view_func=show_event)
app.add_url_rule('/events/<id>/edit', view_func=edit_event, methods=['GET', 'POST'])
app.add_url_rule('/events/<id>/delete', view_func=delete_event)
app.add_url_rule('/events/<id>/join', view_func=join_event, methods=['GET', 'POST'])
app.add_url_rule('/events/<id>/leave', view_func=leave_event, methods=['GET', 'POST'])
app.add_url_rule('/dogs/create', view_func=create_dog, methods=['GET', 'POST'])
app.add_url_rule('/dogs/<id>', view_func=show_dog)
app.add_url_rule('/dogs/<id>/upload', view_func=edit_dog_picture, methods=['POST'])
app.add_url_rule('/dogs/<id>/edit', view_func=edit_dog, methods=['GET', 'POST'])
app.add_url_rule('/dogs/<id>/delete', view_func=delete_dog)
app.add_url_rule('/users', view_func=show_users)
app.add_url_rule('/users/<id>', view_func=show_user)
app.add_url_rule('/get_dogs', view_func=show_users_dogs, methods=['POST'])
app.add_url_rule('/users/<id>/activate', view_func=activate_user)
app.add_url_rule('/users/<id>/edit', view_func=edit_user, methods=['GET', 'POST'])
app.add_url_rule('/users/<id>/delete', view_func=delete_user)
app.add_url_rule('/messages/<id>/delete', view_func=delete_message)
app.add_url_rule('/events/<id>/messages/create', view_func=create_message, methods=['POST'])

