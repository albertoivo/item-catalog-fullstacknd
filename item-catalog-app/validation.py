from model import Category, Item, User, db


# check if user is logged in
def isUserLoggedIn(login_session):
    return 'username' in login_session


# validate the item form
def isItemFormValid(form):
    return form['title'] and form['category']


# check if the item is repeated
def isItemRepeated(category_id, item_title):
    cat = Category.query.filter_by(id=category_id).first()
    item = Item.query.filter_by(title=item_title, category=cat).first()
    return True if item else False


# Check if the picture is have an allowed extension
def allowed_file(filename):
    ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
