from config import app
from controller_functions import index, register, login, logout, dashboard

app.add_url_rule('/', view_func=index)
app.add_url_rule('/register', view_func=register, methods=['POST'])
app.add_url_rule('/login', view_func=login, methods=['POST'])
app.add_url_rule('/logout', view_func=logout)
app.add_url_rule('/dashboard', view_func=dashboard)
app.add_url_rule('/variable/create', view_func=hold, methods=['POST'])
app.add_url_rule('/variable/<id>', view_func=hold)
app.add_url_rule('/variable/<id>/edit', view_func=hold, methods=['GET', 'POST'])
app.add_url_rule('/variable/<id>/delete', view_func=hold)

