from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from model import Category, Item, db

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///itemcatalog.db'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = False


#   category 1   #

cat = Category(name='Car')
db.session.add(cat)
db.session.commit()

item1 = Item(title='EcoSport', description='SUV', category=cat)
db.session.add(item1)
db.session.commit()

item2 = Item(title='Civic', description='Sedan', category=cat)
db.session.add(item2)
db.session.commit()

item3 = Item(title='Focus', description='hatch', category=cat)
db.session.add(item3)
db.session.commit()

#   category 2   #

cat = Category(name='Movies')
db.session.add(cat)
db.session.commit()

item1 = Item(title='InterStellar', description='Fiction', category=cat)
db.session.add(item1)
db.session.commit()

item2 = Item(title='Saving Private Ryan', description='Drama', category=cat)
db.session.add(item2)
db.session.commit()
