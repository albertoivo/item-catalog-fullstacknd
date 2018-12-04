#!/usr/bin/env python
import random
import string
import datetime
from flask import Flask, jsonify, render_template, session as login_session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFError
import crud
from category.category import category
from item.item import item
from login.google import google, csrf

APPLICATION_NAME = "Catalog Item Application"

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///itemcatalog.db'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = False

SQLAlchemy(app)

# Blueprints register
app.register_blueprint(google)
app.register_blueprint(category)
app.register_blueprint(item)

# Protect application from third party attack
csrf.init_app(app)


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


@app.route('/api/help', methods = ['GET'])
def help():
    """Print available functions."""
    func_list = {}
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            func_list[rule.rule] = app.view_functions[rule.endpoint].__doc__
    return jsonify(func_list)


@app.route('/login')
def show_login():
    """show the login screen"""
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


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
