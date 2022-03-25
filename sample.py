from flask import Flask, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sample.db'
app.config['SQLALCHEMY_ECHO']=True
db = SQLAlchemy(app)

class Database(db.Model):
  __tablename__ = "database"
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer)
  name = db.Column(db.String(100), nullable=False)

class Table(db.Model):
  __tablename__ = "table"
  id = db.Column(db.Integer, primary_key=True)
  database_id = db.Column(db.Integer, nullable=False)
  name = db.Column(db.String(100), nullable=False)

@app.before_first_request
def init():
  db.create_all()

@app.route("/sqllist")
def sqllist():
  databases = Database.query.all()
  tables = Table.query.all()
  return render_template("sqllist.html", databases=databases, tabales=tables)


@app.route("/sqlregister", methods=['GET', 'POST'])
def sqlregister():
  if request.method =="POST":
    name = request.form.get("name")
    file = request.files['file']

    print(file)

    with open(file, "r") as f:
      print(f.read())

    # database = Database(user_id=,name=)
    # table = Table(database_id=,name=)

    # db.session.add(database, table)
    # db.session.commit()

    return redirect("/sqllist")
  else:
    return render_template("sqlregister.html")


if __name__ == "__main__":
  app.run(debug=True)