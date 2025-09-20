from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.ext.associationproxy import association_proxy
from marshmallow import Schema, fields

# ----- SQLAlchemy setup with naming convention -----
metadata = MetaData(
    naming_convention={
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    }
)
db = SQLAlchemy(metadata=metadata)

# ===================================================
# Models
# ===================================================

class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    # A customer has many reviews
    reviews = db.relationship(
        'Review',
        back_populates='customer',
        cascade='all, delete-orphan'
    )

    # Association proxy: a customer has many items THROUGH reviews
    items = association_proxy('reviews', 'item')

    def __repr__(self):
        return f'<Customer {self.id}, {self.name}>'


class Item(db.Model):
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    price = db.Column(db.Float)

    # An item has many reviews
    reviews = db.relationship(
        'Review',
        back_populates='item',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Item {self.id}, {self.name}, {self.price}>'


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String)

    # Foreign keys
    customer_id = db.Column(
        db.Integer,
        db.ForeignKey('customers.id'),
        nullable=True
    )
    item_id = db.Column(
        db.Integer,
        db.ForeignKey('items.id'),
        nullable=True
    )

    # Relationships back to Customer and Item
    customer = db.relationship('Customer', back_populates='reviews')
    item = db.relationship('Item', back_populates='reviews')

    def __repr__(self):
        return f'<Review {self.id}, customer_id={self.customer_id}, item_id={self.item_id}>'

# ===================================================
# Marshmallow Schemas
# ===================================================
# Notes on recursion handling:
# - CustomerSchema and ItemSchema include their list of reviews, but each nested
#   review EXCLUDES the back-reference fields ('customer' and/or 'item') so we
#   don’t loop forever.
# - ReviewSchema INCLUDES a nested (shallow) customer and item, but each of those
#   excludes their 'reviews' collections to prevent recursion.

class CustomerSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    # Include reviews but strip their 'customer' and 'item' fields
    reviews = fields.Nested(
        lambda: ReviewSchema(exclude=('customer', 'item')),
        many=True
    )


class ItemSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    price = fields.Float()
    # Include reviews but strip their 'item' and 'customer' fields
    reviews = fields.Nested(
        lambda: ReviewSchema(exclude=('item', 'customer')),
        many=True
    )


class ReviewSchema(Schema):
    id = fields.Integer()
    comment = fields.String()
    # Shallow embed of customer and item (exclude their 'reviews' to avoid cycles)
    customer = fields.Nested(lambda: CustomerSchema(exclude=('reviews',)), allow_none=True)
    item = fields.Nested(lambda: ItemSchema(exclude=('reviews',)), allow_none=True)
