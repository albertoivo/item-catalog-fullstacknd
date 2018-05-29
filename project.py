from flask import Flask, jsonify, render_template, request
from flask import flash, make_response, redirect
from flask import session as login_session

from flask_sqlalchemy import SQLAlchemy

from database_setup import Category, Item, User, db

import random
import string
import json
import httplib2
import requests

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Item Application"


app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///itemcatalog.db'
db = SQLAlchemy(app)


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


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
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
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
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'

        # Store the access token in the session for later use.
        login_session['access_token'] = access_token
        login_session['gplus_id'] = gplus_id

        # see if user exists, if it doesn't make a new one
        user_id = getUserID(login_session['email'])
        if not user_id:
            user_id = createUser(login_session)
        login_session['user_id'] = user_id

        # Get user info
        userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token': access_token, 'alt': 'json'}
        answer = requests.get(userinfo_url, params=params)

        data = answer.json()

        login_session['username'] = data['name']
        login_session['picture'] = data['picture']
        login_session['email'] = data['email']

        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    try:
        # see if user exists, if it doesn't make a new one
        user_id = getUserID(login_session['email'])
        if not user_id:
            user_id = createUser(login_session)
        login_session['user_id'] = user_id
    except:
        pass

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])

    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    db.session.add(newUser)
    db.session.commit()
    user = db.session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = db.session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):

    try:
        user = db.session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

def delLoginSession(login_session):
    del login_session['access_token']
    del login_session['gplus_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']

# DISCONNECT - Revoke a current user's token and reset their login_session
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
        delLoginSession(login_session)

        # response = make_response(json.dumps('Successfully disconnected.'), 200)
        # response.headers['Content-Type'] = 'application/json'
        return redirect('/')#, response
    else:
        # Reset the user's sesson.
        delLoginSession(login_session)

        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Main screen
@app.route('/')
def main():
    cats = Category.query.all()
    latest_items = Item.query.order_by(Item.created.desc()).limit(10).all()
    return render_template('catalog.html', categories=cats, items=latest_items, main_screen=True, login_session=login_session)


# Get all Items by a selected Category
@app.route('/catalog/<string:category_name>/items')
def getItemsByCategory(category_name):
    cats = Category.query.all()
    cat = Category.query.filter_by(name=category_name).first()
    items_by_category = Item.query.filter_by(category=cat).all()
    return render_template('catalog.html', categories=cats, items=items_by_category)


# Get the selected item description
@app.route('/catalog/<string:category_name>/<string:item_title>')
def getItem(category_name, item_title):
    cats = Category.query.all()
    cat = Category.query.filter_by(name=category_name).first()
    item = Item.query.filter_by(title=item_title, category=cat).first()
    return render_template('item.html', categories=cats, item=item)


@app.route('/category/new', methods=['GET','POST'])
def newCategory():
    if 'username' not in login_session:
        return render_template('forbidden.html')
    if request.method == 'POST':
        return redirect(url_for('main'))
    else:
        return render_template('newCategory.html')


@app.route('/item/new', methods=['GET','POST'])
def newItem():
    if 'username' not in login_session:
        return render_template('forbidden.html')
    if request.method == 'POST':
        return redirect(url_for('main'))
    else:
        return render_template('newItem.html')


# JSON APIs to view Catalog Information
@app.route('/catalog.json')
def catalogJSON():
    categories = Category.query.all()
    items = Item.query.all()
    catalog = {"Category": [cat.serialize for cat in categories]}
    for cat in catalog["Category"]:
        cat["item"] = [
            item.serialize for item in items if item.cat_id == cat['id']]
    return jsonify(catalog)


if __name__ == '__main__':
    app.secret_key = '_ROZOjB0Ph1aBQrSS_n1gD58'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
