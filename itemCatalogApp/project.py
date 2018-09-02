#!/usr/bin/env python

from flask import Flask, jsonify, render_template, request
from flask import flash, make_response, redirect, url_for
from flask import session as login_session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, CSRFError
from model import Category, Item, User, db
from validation import isUserLoggedIn, isItemFormValid
from validation import isItemRepeated, allowed_file
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
from werkzeug.utils import secure_filename
import os
import crud
import json
import string
import random
import requests
import datetime
import httplib2
import user_helper

# Protect application from third party attack
csrf = CSRFProtect()

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/img/items')

# client secrets for google sign in
CLIENT_ID = json.loads(open('client_secrets.json',
                            'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Item Application"

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///itemcatalog.db'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = False

csrf.init_app(app)

db = SQLAlchemy(app)

FORBIDDEN_ERROR_MSG = 'Service for authenticated users only.'


# Create anti-forgery state token
@app.route('/login')
def showLogin():
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
        user_id = user_helper.getUserID(login_session['email'])
        if not user_id:
            user_id = user_helper.createUser(login_session)
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
        user_id = user_helper.getUserID(login_session['email'])
        if not user_id:
            user_id = user_helper.createUser(login_session)
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

    userID = user_helper.getUserID(login_session['email'])
    if not userID:
        user_helper.createUser(login_session)

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
        user_helper.delLoginSession(login_session)

        # response = make_response(
        #   json.dumps('Successfully disconnected.'), 200)
        # response.headers['Content-Type'] = 'application/json'
        return redirect('/')  # , response
    else:
        # Reset the user's sesson.
        user_helper.delLoginSession(login_session)

        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Main screen
@app.route('/')
def main():
    cats = crud.allCategories()
    latest_items = crud.latestItem()
    return render_template(
        'catalog.html',
        categories=cats,
        items=latest_items,
        main_screen=True,
        login_session=login_session)


# Get all Items by a selected Category
@app.route('/catalog/<string:category_name>/items')
def getItemsByCategory(category_name):
    cats = crud.allCategories()
    items_by_category = crud.itemsByCategory(category_name)
    return render_template(
        'catalog.html',
        categories=cats,
        qty=len(items_by_category),
        items=items_by_category,
        login_session=login_session)


# Get the selected item description
@app.route('/catalog/<string:category_name>/<string:item_title>')
def getItem(category_name, item_title):
    cats = crud.allCategories()
    item = crud.item(category_name, item_title)
    return render_template(
        'item.html', categories=cats, item=item, login_session=login_session)


# Add Category
@app.route('/category/new', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        app.logger.error(FORBIDDEN_ERROR_MSG)
        return render_template('forbidden.html')
    if request.method == 'POST':
        user = user_helper.getUserByEmail(login_session['email'])
        newCategory = Category(name=request.form['name'], user=user)
        crud.newCategory(newCategory)
        flash(u'%s Successfully Created' % newCategory.name, 'success')
        return redirect(url_for('main'))
    else:
        return render_template(
            'new_category.html', login_session=login_session)


# Edit Category
@app.route('/category/<string:category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):
    if 'username' not in login_session:
        app.logger.error(FORBIDDEN_ERROR_MSG)
        return render_template('forbidden.html')

    if request.method == 'POST':
        name = request.form['name']
        if name:
            crud.editCategory(category_id, name)
            flash(u'\"%s\" Successfully Edited' % name, 'success')
    else:
        cat = crud.category(category_id)
        return render_template(
            'new_category.html', category=cat, login_session=login_session)

    return redirect(url_for('main'))


# Delete Category
@app.route('/category/<string:cat_id>/delete')
def deleteCategory(cat_id):
    if 'username' not in login_session:
        app.logger.error(FORBIDDEN_ERROR_MSG)
        return render_template('forbidden.html')

    crud.deleteCategory(cat_id)

    app.logger.info('category %s deleted.' % cat_id)
    flash(u'Category Successfully Deleted', 'success')

    return redirect(url_for('main'))


# Add Item
@app.route('/item/new', methods=['GET', 'POST'])
def newItem():
    if not isUserLoggedIn(login_session):
        app.logger.error(FORBIDDEN_ERROR_MSG)
        return render_template('forbidden.html')

    if request.method == 'POST':

        cats = crud.allCategories()

        if not isItemFormValid(request.form):
            flash(u'Item title and category are both mandatory', 'error')
            return render_template(
                'new_item.html', categories=cats, login_session=login_session)

        item_title = request.form['title']
        cat_id = request.form['category']

        if isItemRepeated(category_id=cat_id, item_title=item_title):
            cat_name = crud.categoryNameById(cat_id)
            flash(
                u'There is an item called %s in category %s' %
                (item_title, cat_name), 'error')

            return render_template(
                'new_item.html', categories=cats, login_session=login_session)

        picture_path = secure_filename(item_title) + "_"
        try:
            picture = request.files['picture']
            if picture and allowed_file(picture.filename):
                picture_path = picture_path + secure_filename(picture.filename)
                picture.save(os.path.join(UPLOAD_FOLDER, picture_path))
        except Exception:
            pass

        email = login_session['email']
        user = user_helper.getUserByEmail(email=email)
        newItem = Item(
            title=request.form['title'],
            description=request.form['description'],
            cat_id=request.form['category'],
            picture_path=picture_path,
            user=user)

        crud.newItem(newItem)

        app.logger.info('Item %s created.' % newItem.title)
        flash(u'\"%s\" Successfully Created' % newItem.title, 'success')

        return redirect(
            url_for('getItemsByCategory', category_name=newItem.category.name))
    else:
        cats = crud.allCategories()
        return render_template(
            'new_item.html', categories=cats, login_session=login_session)


# Delete Item
@app.route('/item/<string:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(item_id):
    if 'username' not in login_session:
        app.logger.error(FORBIDDEN_ERROR_MSG)
        return render_template('forbidden.html', error=FORBIDDEN_ERROR_MSG)

    item = crud.itemById(item_id)
    cat_name = item.category.name
    user_id = user_helper.getUserID(login_session['email'])
    user = user_helper.getUserInfo(user_id)
    if user.email == item.user.email:
        crud.deleteItem(item_id)
    else:
        error = 'You can delete only items that you created!'
        return render_template('forbidden.html', error=error)

    app.logger.info('Item %s deleted' % item_id)
    flash(u'Item Successfully Deleted', 'success')

    return redirect(url_for('getItemsByCategory', category_name=cat_name))


# Edit Item
@app.route('/item/<string:item_id>/edit', methods=['GET', 'POST'])
def editItem(item_id):
    if 'username' not in login_session:
        app.logger.error(FORBIDDEN_ERROR_MSG)
        return render_template('forbidden.html', error=FORBIDDEN_ERROR_MSG)

    cats = crud.allCategories()
    itemToBeEdited = crud.itemById(item_id)

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        cat_id = request.form['category']

        if itemToBeEdited.title != title:
            if isItemRepeated(category_id=cat_id, item_title=title):
                cat_name = crud.categoryNameById(cat_id)
                flash(
                    u'There is an item called %s in category %s' %
                    (title, cat_name), 'error')

                return render_template(
                    'new_item.html',
                    categories=cats,
                    login_session=login_session)

        picture_path = itemToBeEdited.picture_path
        try:
            picture = request.files['picture']
            if picture and allowed_file(picture.filename):
                try:
                    # in case there isn't a pic before, it raises an excpetion
                    os.remove(
                        os.path.join(UPLOAD_FOLDER,
                                     itemToBeEdited.picture_path))
                finally:
                    picture_path = "%s_%s" % (secure_filename(title),
                                              secure_filename(
                                                  picture.filename))
                    picture.save(os.path.join(UPLOAD_FOLDER, picture_path))
        except Exception:
            pass

        user_id = user_helper.getUserID(login_session['email'])
        user = user_helper.getUserInfo(user_id)
        if user.email == itemToBeEdited.user.email:
            crud.editItem(item_id, title, description, picture_path, cat_id)
        else:
            error = 'You can edit only items the you created!'
            return render_template('forbidden.html', error=error)

        flash(u'Item Successfully Edited', 'success')
    else:
        return render_template(
            'new_item.html',
            item=itemToBeEdited,
            categories=cats,
            login_session=login_session)

    return redirect(url_for('main'))


@app.route('/profile')
def profile():
    app.logger.info('View Profile')
    return render_template('profile.html', login_session=login_session)


# JSON APIs to view Catalog Information
@app.route('/catalog.json')
def catalogJSON():
    categories = crud.allCategories()
    items = crud.allItems()
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
    app.debug = False
    app.logger.info('App started at %s' % datetime.datetime.now())
    app.run(port=80)
    app.logger.info('App stopped at %s' % datetime.datetime.now())
