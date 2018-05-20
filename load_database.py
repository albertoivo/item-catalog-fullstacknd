from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

#   category 1   #

cat = Category(name='Car')
session.add(cat)
session.commit()

item1 = Item(title='EcoSport', description='SUV', category=cat)
session.add(item1)
session.commit()

item2 = Item(title='Civic', description='Sedan', category=cat)
session.add(item2)
session.commit()

item3 = Item(title='Focus', description='hatch', category=cat)
session.add(item3)
session.commit()

#   category 2   #

cat = Category(name='Movies')
session.add(cat)
session.commit()

item1 = Item(title='InterStellar', description='Fiction', category=cat)
session.add(item1)
session.commit()

item2 = Item(title='Saving Private Ryan', description='Drama', category=cat)
session.add(item2)
session.commit()
