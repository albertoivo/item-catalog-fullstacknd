from flask import Blueprint, render_template, request, flash, redirect, url_for, \
    session as login_session
import crud
import user_helper
import constants
from model import Item
from validation import is_user_logged_in, is_item_form_valid, is_item_repeated

item = Blueprint('item', __name__, template_folder='templates')


# Get all Items by a selected Category
@item.route('/catalog/<string:category_name>/items')
def get_items_by_category(category_name):
    cats = crud.all_categories()
    items_by_category = crud.items_by_category(category_name)
    return render_template(
        'catalog.html',
        categories=cats,
        qty=len(items_by_category),
        items=items_by_category,
        login_session=login_session)


# Get the selected item description
@item.route('/catalog/<string:category_name>/<string:item_title>')
def get_item(category_name, item_title):
    cats = crud.all_categories()
    item = crud.item(category_name, item_title)
    return render_template(
        'item.html', categories=cats, item=item, login_session=login_session)


# Add Item
@item.route('/item/new', methods=['GET', 'POST'])
def new_item():
    if not is_user_logged_in(login_session):
        return render_template('forbidden.html')

    if request.method == 'POST':

        cats = crud.all_categories()

        if not is_item_form_valid(request.form):
            flash(u'Item title and category are both mandatory', 'error')
            return render_template(
                'new_item.html', categories=cats, login_session=login_session)

        item_title = request.form['title']
        cat_id = request.form['category']

        if is_item_repeated(category_id=cat_id, item_title=item_title):
            cat_name = crud.category_name_by_id(cat_id)
            flash(
                u'There is an item called %s in category %s' %
                (item_title, cat_name), 'error')

            return render_template(
                'new_item.html', categories=cats, login_session=login_session)

        email = login_session['email']
        user = user_helper.get_user_by_email(email=email)
        new_item = Item(
            title=request.form['title'],
            description=request.form['description'],
            cat_id=request.form['category'],
            picture_path=request.form['picture'],
            user=user)

        crud.new_item(new_item)

        flash(u'\"%s\" Successfully Created' % new_item.title, 'success')

        return redirect(
            url_for('item.get_items_by_category',
                    category_name=new_item.category.name))
    else:
        cats = crud.all_categories()
        return render_template(
            'new_item.html', categories=cats, login_session=login_session)


# Delete Item
@item.route('/item/<string:item_id>/delete', methods=['GET', 'POST'])
def delete_item(item_id):
    if 'username' not in login_session:
        return render_template(
            'forbidden.html',
            error=constants.FORBIDDEN_ERROR_MSG)

    item = crud.item_by_id(item_id)
    cat_name = item.category.name
    user_id = user_helper.get_user_id(login_session['email'])
    user = user_helper.get_user_info(user_id)
    if user.email == item.user.email:
        crud.delete_item(item_id)
    else:
        error = 'You can delete only items that you created!'
        return render_template('forbidden.html', error=error)

    flash(u'Item Successfully Deleted', 'success')

    return redirect(
        url_for(
            'item.get_items_by_category',
            category_name=cat_name))


# Edit Item
@item.route('/item/<string:item_id>/edit', methods=['GET', 'POST'])
def edit_item(item_id):
    if 'username' not in login_session:
        return render_template(
            'forbidden.html',
            error=constants.FORBIDDEN_ERROR_MSG)

    cats = crud.all_categories()
    item_to_be_edited = crud.item_by_id(item_id)

    if request.method == 'POST':
        title = request.form['title']
        picture_path = request.form['picture']
        description = request.form['description']
        cat_id = request.form['category']

        if item_to_be_edited.title != title:
            if is_item_repeated(category_id=cat_id, item_title=title):
                cat_name = crud.category_name_by_id(cat_id)
                flash(
                    u'There is an item called %s in category %s' %
                    (title, cat_name), 'error')

                return render_template(
                    'new_item.html',
                    categories=cats,
                    login_session=login_session)

        user_id = user_helper.get_user_id(login_session['email'])
        user = user_helper.get_user_info(user_id)
        if user.email == item_to_be_edited.user.email:
            crud.edit_item(item_id, title, description, picture_path, cat_id)
        else:
            return render_template('forbidden.html', error=constants.AUTH_ERROR_EDIT_ITEM)

        flash(u'Item Successfully Edited', 'success')
    else:
        return render_template(
            'new_item.html',
            item=item_to_be_edited,
            categories=cats,
            login_session=login_session)

    return redirect(url_for('main'))
