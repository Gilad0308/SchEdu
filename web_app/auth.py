from flask import Blueprint, render_template, redirect, url_for, request, flash
from .models import User
from . import db
# Hash function has only one-way. Given a hashed password you can't find the original password.
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user


auth = Blueprint('auth', __name__)


# If GET request - displays the login page
# If POST request - checks the email exists and the password is correct.
# If so, loggs in the user and redirects to the home page.
# If not displays the login page again with a suitable message.
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)  # The user will stay connected as long as the server is still running, and the user hasn't logged out or cleared browsing history.
                flash('Logged in successfully!', category='success')
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash("No user with that Email.", category='error')

    return render_template("login.html", user=current_user)


# If GET request - displays the sign up page
# If POST request - checks the email doesn't exist.
# If so, creates a new user and adds it to the database. Then, redirects to the home page. 
# If not displays the sign up page again with a suitable message.
@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form['email']
        name = request.form['name']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists', category='error')

        else:
            # add user to database
            new_user = User(email=email, name=name, password=generate_password_hash(password, method="sha256"))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)  # The user will stay connected as long as the server is still running, and the user hasn't logged out or cleared browsing history.
            flash("Account created!", category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up.html", user=current_user)


# Loggs out the user
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
