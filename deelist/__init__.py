from __future__ import absolute_import
import logging
import requests
from flask import Flask, redirect, url_for, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user,\
        logout_user, current_user
from os import environ

from .utils.list_api import ListWrapper
from .utils.oauth import OAuthSignIn

app = Flask(__name__)
log = logging.getLogger('flask').setLevel(logging.DEBUG)

app.config['SQLALCHEMY_DATABASE_URI'] = environ.get("DB_URI")
app.secret_key = environ.get("SECRET_KEY")
app.config['OAUTH_CREDENTIALS'] = {
    'amazon':{
        'id': environ.get("AMAZON_ID"),
        'secret': environ.get("AMAZON_SECRET")
    }
}

db = SQLAlchemy(app)
lm = LoginManager(app)
lm.init_app(app)
lm.login_view = 'index'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    nickname = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=True)


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, nickname=username, email=email)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('index'))
