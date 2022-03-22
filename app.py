from flask import Flask, flash, redirect, url_for, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker

# appを初期化
app = Flask(__name__)
app.secret_key = "kazuki"

db = "postgresql+psycopg2://postgres:....@192.168.1.3:5432/mydb"

# Engineの作成
engine = sqlalchemy.create_engine(
    db,
    encoding="utf-8",
    echo=True
)

# SQLAlchemy の設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.py'

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

# DB とつなぐ
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    hash = db.Column(db.String(100), nullable=False)

class Preuser(db.Model):
    __tablename__ = "preusers"

    session_id = db.Column(db.Integer, primary_key=True)

class Database(db.Model):
    __tablename__ = 'databases'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer)
    session_id = db.Column(db.Integer)

class Table(db.Model):
    __tablename__ = "tables"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    database_id = db.Column(db.Integer, nullable=False)

@app.route("/dblist", methods=["GET", "POST"])
def dblist():
    # postの場合
    if request.method == "POST":
        # 選択したテーブルIDを取得
        table_ids = request.form.getlist("table")

        # 選択した個数の例外処理
        if len(table_ids) == 0: # 選択されていない場合
            flash("テーブルを選択してください", "failed")
            return redirect("/dblist")
        elif len(table_ids) > 3: # 4つ以上選択されている場合
            flash("テーブルを3つまで選択してください", "failed")
            return redirect("/dblist")
        
        # 画面遷移
        if len(table_ids) == 3: # テーブル1が選択されている時
            return redirect(url_for('dblist', table1_id=table_ids[0], table2_id=table_ids[1], table3_id=table_ids[2]))
        elif len(table_ids) == 2:
            return redirect(url_for('dblist', table1_id=table_ids[0], table2_id=table_ids[1]))
        elif len(table_ids) == 1:
            return redirect(url_for('dblist', table1_id=table_ids[0]))

    # getの場合
    else:
        databases = db.session.execute("SELECT * FROM databases WHERE user_id = ?", "1")
        print(database)
        # return render_template("dblist.html")
        # データベースを取得
        if session["user_id"]: # ログイン時
            databases = db.session.execute("SELECT * FROM databases WHERE user_id = ?", session["user_id"])
        elif session["session_id"]: # 未ログイン時
            databases = db.session.execute("SELECT * FROM databases WHERE session_id = ?", session["session_id"])
        else: # エラー時
            flash("エラーが発生しました", "failed")
            return redirect("/")

        # 該当するデータベースがない場合
        if not databases:
            flash("データベースを登録してください", "failed")
            return render_template("dbregister.html")
        
        # データベースidと合致するテーブルを取得
        tables = []
        for database in databases:
            rows = db.session.execute("SELECT * FROM tables WHERE database_id = ?", database["id"])
            if tables:
                tables.append(rows)
            else:
                tables = rows

        # 画面右側に表示するテーブル
        table1_id = request.args.get("table1_id")
        table2_id = request.args.get("table2_id")
        table3_id = request.args.get("table3_id")

        # 画面遷移
        if table1_id: # テーブル1が選択されている時
            try:
                table1 = db.session.execute("SELECT * FROM ?", table1_id)
            except:
                flash("エラーが発生しました", "failed")
                return redirect("/")
            table1_name = db.execute("SELECT name FROM tables WHERE id = ?", table1_id)[0]["name"]
            table1_columns = db.session.execute("SELECT column_name AS name FROM information_schema.columns WHERE table_name = ?", table1_id)
        else: # テーブルが選択されていない時
            return render_template("dblist.html", databases=databases, tables=tables)
        if table2_id: # テーブル2が選択されている時
            try:
                table2 = db.session.execute("SELECT * FROM ?", table2_id)
            except:
                flash("エラーが発生しました", "failed")
                return redirect("/")
            table2_name = db.execute("SELECT name FROM tables WHERE id = ?", table2_id)[0]["name"]
            table2_columns = db.session.execute("SELECT column_name AS name FROM information_schema.columns WHERE table_name = ?", table2_id)
        else: # テーブル1のみが選択されている時
            return render_template("dblist.html", databases=databases, tables=tables, table1_id=table1_id, table1=table1, table1_columns=table1_columns, table1_name=table1_name)
        if table3_id: # テーブル3が選択されている時
            try:
                table3 = db.session.execute("SELECT * FROM ?", table3_id)
            except:
                flash("エラーが発生しました", "failed")
                return redirect("/")
            table3_name = db.execute("SELECT name FROM tables WHERE id = ?", table3_id)[0]["name"]
            table3_columns = db.session.execute("SELECT column_name AS name FROM information_schema.columns WHERE table_name = ?", table3_id)
            return render_template("dblist.html", databases=databases, tables=tables, table1_id=table1_id, table1=table1, table1_columns=table1_columns, table1_name=table1_name, table2_id=table2_id, table2=table2, table2_columns=table2_columns, table2_name=table2_name, table3_id=table3_id, table3=table3, table3_columns=table3_columns, table3_name=table3_name)
        else: # テーブル1とテーブル2のみが選択されている時
            return render_template("dblist.html", databases=databases, tables=tables, table1_id=table1_id, table1=table1, table1_columns=table1_columns, table1_name=table1_name, table2_id=table2_id, table2=table2, table2_columns=table2_columns, table2_name=table2_name)

if __name__ == "__main__": # 直接起動用
    app.run(debug=True)
