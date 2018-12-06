from model import Category, Item


# check if user is logged in
def is_user_logged_in(login_session):
    return 'username' in login_session


# validate the item form
def is_item_form_valid(form):
    return form['title'] and form['category']


# check if the item is repeated
def is_item_repeated(category_id, item_title):
    cat = Category.query.filter_by(id=category_id).first()
    item = Item.query.filter_by(title=item_title, category=cat).first()
    return True if item else False


# Check if the picture is have an allowed extension
def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return filename.rsplit('.', 1)[1].lower() in allowed_extensions
