import httplib2
import requests
import json
import os
import user_helper
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
from flask import Blueprint, request, flash, make_response, redirect, url_for,\
    session as login_session
from flask_wtf import CSRFProtect

csrf = CSRFProtect()

google = Blueprint('google', __name__, template_folder='templates')


# Google SignIn Client Secrets
CURRENT_DIR = os.path.dirname(__file__)
client_secrets = os.path.join(CURRENT_DIR, 'google.json')
CLIENT_ID = json.loads(open(client_secrets, 'r').read())['web']['client_id']


# Login - Google
@csrf.exempt
@google.route('/gconnect', methods=['POST'])
def gconnect():
    """Connect with Google SignIn"""

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
        oauth_flow = flow_from_clientsecrets(client_secrets, scope='')
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
@google.route('/logout')
def gdisconnect():
    """Disconnect from google"""

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
        return redirect(url_for('main'))
    else:
        # Reset the user's sesson.
        user_helper.delete_login_session(login_session)

        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'))
        response.headers['Content-Type'] = 'application/json'
        return response
