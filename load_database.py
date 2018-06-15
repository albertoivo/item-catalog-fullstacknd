from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from model import User, Category, Item, db

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///itemcatalog.db'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = False

# user 1 #

user1 = User(
    name="Alberto Ivo",
    email="albertoivo@gmail.com",
    picture=
    "https://lh5.googleusercontent.com/-smnqdptNz7c/AAAAAAAAAAI/AAAAAAAAAAA/IXBlsOnx2yY/photo.jpg"
)
db.session.add(user1)
db.session.commit()

user2 = User(
    name="Marianne Vieira",
    email="mariannefarias@gmail.com",
    picture=
    "https://lh5.googleusercontent.com/-smnqdptNz7c/AAAAAAAAAAI/AAAAAAAAAAA/IXBlsOnx2yY/photo.jpg"
)
db.session.add(user2)
db.session.commit()

#   category 1   #

cat = Category(name='Car', user=user2)
db.session.add(cat)
db.session.commit()

item1 = Item(
    title='EcoSport',
    description='SUV',
    category=cat,
    picture_path="ecosport.jpeg",
    user=user1)
db.session.add(item1)
db.session.commit()

item2 = Item(
    title='Civic',
    description='Sedan',
    category=cat,
    picture_path="civic.png",
    user=user2)
db.session.add(item2)
db.session.commit()

item3 = Item(
    title='Focus',
    description='hatch',
    category=cat,
    picture_path="focus.jpeg",
    user=user1)
db.session.add(item3)
db.session.commit()

#   category 2   #

cat = Category(name='Movies', user=user1)
db.session.add(cat)
db.session.commit()

item1 = Item(
    title='InterStellar', description='Fiction', category=cat, user=user1)
db.session.add(item1)
db.session.commit()

item2 = Item(
    title='Saving Private Ryan', description='Drama', category=cat, user=user2)
db.session.add(item2)
db.session.commit()
