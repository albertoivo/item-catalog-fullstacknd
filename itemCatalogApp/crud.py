from model import Category, Item, db


# find all categories
def all_categories():
    return Category.query.all()


# find all items
def all_items():
    return Item.query.all()


# find the latest items
def latest_item():
    return Item.query.order_by(Item.created.desc()).limit(10)


# find Items By Category
def items_by_category(category_name):
    cat = Category.query.filter_by(name=category_name).first_or_404()
    return Item.query.filter_by(category=cat).all()


# get the whole item by category and title
def item(category_name, item_title):
    cat = Category.query.filter_by(name=category_name).first_or_404()
    return Item.query.filter_by(title=item_title, category=cat).first_or_404()


# get item by id
def item_by_id(item_id):
    return Item.query.filter_by(id=item_id).first_or_404()


# create a new category
def new_category(new_category):
    db.session.add(new_category)
    db.session.commit()


# find a category by id
def category(category_id):
    return Category.query.filter_by(id=category_id).first_or_404()


# get the category name
def category_name_by_id(category_id):
    return Category.query.filter_by(id=category_id).first().name


# edit a category
def edit_category(category_id, name):
    category_to_be_edited = category(category_id)
    category_to_be_edited.name = name
    db.session.commit()


# delete a category
def delete_category(cat_id):
    cat = Category.query.filter_by(id=cat_id).first_or_404()
    db.session.delete(cat)
    db.session.commit()


# create a new Item
def new_item(new_item):
    db.session.add(new_item)
    db.session.commit()


# delete the item
def delete_item(item_id):
    item = item_by_id(item_id)
    db.session.delete(item)
    db.session.commit()


# edit item
def edit_item(item_id, title, description, picture_path, cat_id):
    item = item_by_id(item_id)
    item.title = title
    item.description = description
    item.picture_path = picture_path
    item.cat_id = cat_id
    db.session.commit()
