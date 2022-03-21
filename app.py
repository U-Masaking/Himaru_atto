from flask import Flask, flash, render_template, session, request
from flask_session import Session
from database import init_db, db
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
import models
import psycopg2
import sqlalchemy


db = "postgresql+psycopg2://postgres:724817tf@192.168.0.26:5432/testDB"

engine = sqlalchemy.create_engine(
    db,
    encoding="utf-8",
    echo=True
)


def create_app():
    app = Flask(__name__)
    app.config.from_object('flask_sample.config.Config')
    init_db(app)
    return app

app = create_app()

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
)

db.create_all()

@app.route('/')
def index_before():

    # userID = session["user_id"]
    transaction_flag = False

    if request.method == "POST":

        query = request.form.get("Query")

        # ユーザーのテーブル全部
        table1 = db.session.execute("SELECT * FROM ?", ユーザーが操作しているデータベース)

        # 一時保存の場合
        if request.form['send'] == 'temporary':
            if transaction_flag == False:
                transaction_flag = True
                db.session.execute("BEGIN;")
            try :
                db.session.execute(query)
                db.session.execute(";")
            except :
                flash("SQL構文が間違っています")
                return render_template("index_before.html")

            # ユーザーが捜査した後のテーブル全部
            table2 = db.session.execute("SELECT * FROM ?", ユーザーが捜査しているtable)

            return render_template("index_before.html", table1, table2, ユーザーが捜査した箇所（結果用）)

        # 実行した場合
        if request.form['send'] == 'execute':
            try :
                db.session.execute(query)
                db.session.execute(";")
            except :
                flash("SQL構文が間違っています")
                return render_template("index_before.html")

            if transaction_flag == True:
                db.execute("COMMIT;")

            flash("データベースが編集されました")

            table = db.session.execute("SELECT * FROM ?", ユーザーが捜査しているtable)

            return render_template("index_before.html", table, )

    if transaction_flag == True:
        db.session.execute("ROLLBACK;")

    return render_template('index_before.html')
