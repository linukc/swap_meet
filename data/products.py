import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Products(SqlAlchemyBase):
    __tablename__ = 'products'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False, index=True)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    location = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    price = sqlalchemy.Column(sqlalchemy.Float, nullable=False)
    photo = sqlalchemy.Column(sqlalchemy.String, nullable=True, default='x3348866-674439124.png')
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now, nullable=False)
    is_private = sqlalchemy.Column(sqlalchemy.Boolean, default=True)

    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    user = orm.relation('User')
    categories = orm.relation("Category", secondary="association", backref="products")
