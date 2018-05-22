from flask import Flask, jsonify, render_template
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Main screen
@app.route('/')
def main():
    categories = session.query(Category).order_by(asc(Category.name))
    return render_template('catalog.html')


# Get all Items by a selected Category
@app.route('/catalog/<string:category_name>/items')
def getItemsByCategory(category_name):
    return render_template('items_by_category.html')


# Get the selected item description
@app.route('/catalog/<string:category_name>/<string:item_title>')
def getItem(category_name, item_title):
    return render_template('item.html')


# JSON APIs to view Catalog Information
@app.route('/catalog.json')
def catalogJSON():
    categories = session.query(Category).all()
    items = session.query(Item).all()
    catalog = {"Category": [cat.serialize for cat in categories]}
    for cat in catalog["Category"]:
        cat["item"] = [
            item.serialize for item in items if item.cat_id == cat['id']]
    return jsonify(catalog)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
