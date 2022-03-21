from database import db
from sqlalchemy import CheckConstraint

class User(db.Model):

	__tablename__ = 'users'

	id = db.Column(db.Serial, primary_key=True)
	name = db.Column(db.Varchar(100), nullable=False)
	address = db.Column(db.Varchar(100), nullable=False)
	hash = db.Column(db.Varchar(100), nullable=False)

	db.relationship('database', backref='users')



class database(db.Model):

	__tablename__ = 'databases'

	id = db.Column(db.Serial, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	session_id = db.Column(db.Integer, db.ForeignKey('preusers.id'))
	naem = db.Column(db.Varchar(100), nullable=False)

	__table_args__ = (CheckConstraint("(user_id = NULL AND preuser_id != NULL) OR (user_id != NULL AND preuser_id = NULL)"))


class preuser(db.Model):
	__tablename__ = "preusers"

	id = db.Column(db.Serial, primary_key=True)

	db.relationship('database', backref='preusers')


class table(db.Model):

	__tablename__ = "tables"

	id = db.Column(db.Serial, primary_key=True)
	name = db.Column(db.Varchar(100), nullable=False)
	database_id = db.Column(db.Integer, nullable=False)
