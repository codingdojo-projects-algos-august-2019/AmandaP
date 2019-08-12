# conveniently, Flask has a jsonify function
from flask import render_template, request, redirect, session, url_for, flash, jsonify
from models import User, users_schema, user_schema
from config import db
from dateutil.parser import parse


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
    user_obj_info = user_info.dump(user_obj)
    return render_template('index.html', user=user_obj_info.data)
