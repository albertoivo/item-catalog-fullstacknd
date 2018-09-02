from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import update
from model import Category, Item, User, db
import os

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/img/items')


# find all categories
def allCategories():
    return Category.query.all()


# find all items
def allItems():
    return Item.query.all()


# find the latest items
def latestItem():
    return Item.query.order_by(Item.created.desc()).limit(10)


# find Items By Category
def itemsByCategory(category_name):
    cat = Category.query.filter_by(name=category_name).first_or_404()
    return Item.query.filter_by(category=cat).all()


# get the whole item by category and title
def item(category_name, item_title):
    cat = Category.query.filter_by(name=category_name).first_or_404()
    return Item.query.filter_by(title=item_title, category=cat).first_or_404()


def itemById(item_id):
    return Item.query.filter_by(id=item_id).first_or_404()


# create a new category
def newCategory(newCategory):
    db.session.add(newCategory)
    db.session.commit()


# find a category by id
def category(category_id):
    return Category.query.filter_by(id=category_id).first_or_404()


# get the category name
def categoryNameById(category_id):
    return Category.query.filter_by(id=category_id).first().name


# edit a category
def editCategory(category_id, name):
    categoryToBeEdited = category(category_id)
    categoryToBeEdited.name = name
    db.session.commit()


# delete a category
def deleteCategory(cat_id):
    cat = Category.query.filter_by(id=cat_id).first_or_404()
    db.session.delete(cat)
    db.session.commit()


# create a new Item
def newItem(newItem):
    db.session.add(newItem)
    db.session.commit()


# delete the item
def deleteItem(item_id):
    item = itemById(item_id)
    if item.picture_path:
        os.remove(os.path.join(UPLOAD_FOLDER, item.picture_path))
    db.session.delete(item)
    db.session.commit()


# edit item
def editItem(item_id, title, description, picture_path, cat_id):
    item = itemById(item_id)
    item.title = title
    item.description = description
    item.picture_path = picture_path
    item.cat_id = cat_id

    db.session.commit()
