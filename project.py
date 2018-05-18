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


# JSON APIs to view Restaurant Information
@app.route('/catalog.json')
def catalogJSON():
    catalog_all = session.query(Category).all()
    items_all = session.query(Item).all()
    catalog = {"Category": [cate.serialize for cate in catalog_all]}
    for cate in catalog["Category"]:
        cate["Item"] = [
            item.serialize for item in items_all if item.cat_id == cate['id']]
    return jsonify(catalog)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
app.run(host='0.0.0.0', port=8000)