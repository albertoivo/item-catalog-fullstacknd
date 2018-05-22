from flask import Flask, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# JSON APIs to view Catalog Information
@app.route('/catalog.json')
def catalogJSON():
    categories = session.query(Category).all()
    items = session.query(Item).all()
    catalog = {"Category": [cat.serialize for cat in categories]}
    for cat in catalog["Category"]:
        cat["Item"] = [
            item.serialize for item in items if item.cat_id == cat['id']]
    return jsonify(catalog)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
