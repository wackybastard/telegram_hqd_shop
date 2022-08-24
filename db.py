from peewee import *


db = SqliteDatabase('bot.db', pragmas={'foreign_keys': 1})


class User(Model):
    id = PrimaryKeyField(unique=True)
    username = CharField()
    is_promo = BooleanField()

    class Meta():
        database = db
        order_by = 'id'


class Category(Model):
    id = PrimaryKeyField(unique=True)
    name = CharField()
    comment = CharField()

    class Meta():
        database = db
        order_by = 'id'


class Product(Model):
    id = PrimaryKeyField(unique=True)
    name = CharField()
    price = IntegerField()
    category_id = ForeignKeyField(Category, backref='products')

    class Meta():
        database = db
        order_by = 'id'


if __name__ == '__main__':
    db.create_tables([User, Category, Product])
