#!/usr/bin/env python

import datetime
import json
import os
import random
import string
import httplib2
import requests
from flask import Flask, jsonify, render_template, request, flash, make_response, redirect, \
  session as login_session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, CSRFError
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import crud
import user_helper
from category.category import category
from item.item import item

APPLICATION_NAME = "Catalog Item Application"

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///itemcatalog.db'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = False

app.register_blueprint(category)
app.register_blueprint(item)

SQLAlchemy(app)

# Google Sign In Client Secrets
CURRENT_DIR = os.path.dirname(__file__)
client_secrets = os.path.join(CURRENT_DIR, 'client_secrets.json')
CLIENT_ID = json.loads(open(client_secrets,
                            'r').read())['web']['client_id']

# Protect application from third party attack
csrf = CSRFProtect()
csrf.init_app(app)


# Create anti-forgery state token
@app.route('/login')
def show_login():
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


# Login - Google
@csrf.exempt
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code, now compatible with Python3
    request.get_data()
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
           access_token)
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'

        # Store the access token in the session for later use.
        login_session['access_token'] = access_token
        login_session['gplus_id'] = gplus_id

        # see if user exists, if it doesn't make a new one
        user_id = user_helper.get_user_id(login_session['email'])
        if not user_id:
            user_id = user_helper.create_user(login_session)
        login_session['user_id'] = user_id

        # Get user info
        userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token': access_token, 'alt': 'json'}
        answer = requests.get(userinfo_url, params=params)

        data = answer.json()

        login_session['username'] = data['name']
        login_session['picture'] = data['picture']
        login_session['email'] = data['email']
        login_session['gplus'] = data['link']

        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    try:
        # see if user exists, if it doesn't make a new one
        user_id = user_helper.get_user_id(login_session['email'])
        if not user_id:
            user_id = user_helper.create_user(login_session)
        login_session['user_id'] = user_id
    except Exception:
        pass

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['gplus'] = data['link']

    user_id = user_helper.get_user_id(login_session['email'])
    if not user_id:
        user_helper.create_user(login_session)

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style = "width: 300px; height: 300px; border-radius: 150px;>'
    flash(u"You are now logged in as %s" % login_session['username'],
          'primary')

    return output


# Logout - Revoke a current user's token and reset their login_session
@app.route('/logout')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's sesson.
        user_helper.delete_login_session(login_session)

        # response = make_response(
        #   json.dumps('Successfully disconnected.'), 200)
        # response.headers['Content-Type'] = 'application/json'
        return redirect('/')  # , response
    else:
        # Reset the user's sesson.
        user_helper.delete_login_session(login_session)

        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'))
        response.headers['Content-Type'] = 'application/json'
        return response


# Main screen
@app.route('/')
def main():
    cats = crud.all_categories()
    latest_items = crud.latest_item()
    return render_template(
        'catalog.html',
        categories=cats,
        items=latest_items,
        main_screen=True,
        login_session=login_session)


@app.route('/profile')
def profile():
    app.logger.info('View Profile')
    return render_template('profile.html', login_session=login_session)


# JSON APIs to view Catalog Information
@app.route('/catalog.json')
def catalog_json():
    categories = crud.all_categories()
    items = crud.all_items()
    catalog = {"Category": [cat.serialize for cat in categories]}
    for cat in catalog["Category"]:
        cat["item"] = [
            item.serialize for item in items if item.cat_id == cat['id']
        ]
    app.logger.info('JSON requested')
    return jsonify(catalog)


# Error Handler
@app.errorhandler(404)
def page_not_found(error):
    app.logger.error(error.description)
    return render_template(
        'page_not_found.html', error=error, login_session=login_session), 404


# Handle a CSRF error that may occur
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    app.logger.error(e.description)
    return render_template('csrf_error.html', reason=e.description), 400


# Main
if __name__ == '__main__':
    app.secret_key = '_ROZOjB0Ph1aBQrSS_n1gD58'
    app.wtf_csrf_secret_key = 'aj@2lL!OA0NU'
    app.debug = True
    app.logger.info('Item Catalog App started at %s' % datetime.datetime.now())
    app.run(host="localhost")
    app.logger.info('Item Catalog App stopped at %s' % datetime.datetime.now())
