from datetime import datetime

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///itemcatalog.db'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = False

db = SQLAlchemy(app)


class User(db.Model):
    """ User table """

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=False)
    picture = db.Column(db.String(250))

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email
        }

    def __repr__(self):
        return '<User %r>' % self.name


class Category(db.Model):
    """ Category table """

    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship(User)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
        }

    def __repr__(self):
        return '<Category %r>' % self.name


class Item(db.Model):
    """ Item table """

    __tablename__ = 'item'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(250))
    picture_path = db.Column(db.String)
    created = db.Column(db.DateTime, nullable=False,
                        default=datetime.utcnow, onupdate=datetime.utcnow)
    cat_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship(
        Category, backref=db.backref("Item", cascade="all,delete"))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship(User)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'cat_id': self.cat_id
        }

    def __repr__(self):
        return '<Item %r>' % self.title


# Create the initial database
db.create_all()
