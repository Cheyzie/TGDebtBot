
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Duty(Base):
    __tablename__ = 'duties'

    id = sa.Column(sa.Integer, primary_key=True)
    lender = sa.Column(sa.String, nullable=False)
    debtor = sa.Column(sa.String, nullable=False)
    amount = sa.Column(sa.Float)


class UserInfo(Base):
    __tablename__='users_info'

    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.String, unique=True, nullable=False)
    user_id = sa.Column(sa.Integer, unique=True)
    chat_id = sa.Column(sa.Integer, unique=True)