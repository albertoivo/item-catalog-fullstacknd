import crud
import user_helper
from flask import Blueprint, render_template, request, flash, redirect, \
    url_for, session as login_session
from model import Category

category = Blueprint('category', __name__, template_folder='templates',
                     url_prefix='/category')


# Add Category
@category.route('/new', methods=['GET', 'POST'])
def new_category():
    """Create a new category"""

    if 'username' not in login_session:
        return render_template('forbidden.html')
    if request.method == 'POST':
        user = user_helper.get_user_by_email(login_session['email'])
        new_category = Category(name=request.form['name'], user=user)
        crud.new_category(new_category)
        flash(u'%s Successfully Created' % new_category.name, 'success')
        return redirect(url_for('main'))
    else:
        return render_template(
            'new_category.html', login_session=login_session)


# Edit Category
@category.route('/<string:category_id>/edit', methods=['GET', 'POST'])
def edit_category(category_id):
    """Edit a category"""

    if 'username' not in login_session:
        return render_template('forbidden.html')
    if request.method == 'POST':
        name = request.form['name']
        if name:
            crud.edit_category(category_id, name)
            flash(u'\"%s\" Successfully Edited' % name, 'success')
    else:
        cat = crud.category(category_id)
        return render_template(
            'new_category.html', category=cat, login_session=login_session)
    return redirect(url_for('main'))


# Delete Category
@category.route('/<string:cat_id>/delete')
def delete_category(cat_id):
    """Delete a category"""

    if 'username' not in login_session:
        return render_template('forbidden.html')
    crud.delete_category(cat_id)
    flash(u'Category Successfully Deleted', 'success')
    return redirect(url_for('main'))
