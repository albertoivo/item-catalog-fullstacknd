from model import User, db


def create_user(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    db.session.add(newUser)
    db.session.commit()
    user = db.session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def get_user_info(user_id):
    try:
        user = db.session.query(User).filter_by(id=user_id).one()
        return user
    except Exception:
        return None


def get_user_id(email):
    try:
        user = db.session.query(User).filter_by(email=email).one()
        return user.id
    except Exception:
        return None


def get_user_by_email(email):
    try:
        return db.session.query(User).filter_by(email=email).one()
    except Exception:
        return None


def delete_login_session(login_session):
    del login_session['access_token']
    del login_session['gplus_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
