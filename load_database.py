from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

cat1 = Category(name='Car')
session.add(cat1)
session.commit()

item1 = Item(title='EcoSport', description='SUV', category=cat1)
session.add(item1)
session.commit()

item2 = Item(title='Civic', description='Sedan', category=cat1)
session.add(item2)
session.commit()

item3 = Item(title='Focus', description='hatchSUV', category=cat1)
session.add(item3)
session.commit()
