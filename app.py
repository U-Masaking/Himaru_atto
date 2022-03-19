import os

from flask import Flask, flash, redirect, url_for, render_template, request, session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import *
from sqlalchemy.orm import *
from flask_sqlalchemy import SQLAlchemy


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

db = SQLAlchemy()

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


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
        if session["user_id"]: # ログイン時
            if len(table_ids) == 3: # 3つ選択した場合
                return redirect(url_for('index_after', table1_id=table_ids[0], table2_id=table_ids[1], table3_id=table_ids[2]))
            elif len(table_ids) == 2: # 2つ選択した場合
                return redirect(url_for('index_after', table1_id=table_ids[0], table2_id=table_ids[1]))
            elif len(table_ids) == 1: # 1つ選択した場合
                return redirect(url_for('index_after', table1_id=table_ids[0]))
        elif session["session_id"]: # 未ログイン時
            if len(table_ids) == 3: # 3つ選択した場合
                return redirect(url_for('index_before', table1_id=table_ids[0], table2_id=table_ids[1], table3_id=table_ids[2]))
            elif len(table_ids) == 2: # 2つ選択した場合
                return redirect(url_for('index_before', table1_id=table_ids[0], table2_id=table_ids[1]))
            elif len(table_ids) == 1: # 1つ選択した場合
                return redirect(url_for('index_before', table1_id=table_ids[0]))

    # getの場合
    else:
        # データベースを取得
        if session["user_id"]: # ログイン時
            databases = db.execute("SELECT * FROM databases WHERE user_id = ?", session["user_id"])
        elif session["session_id"]: # 未ログイン時
            databases = db.execute("SELECT * FROM databases WHERE session_id = ?", session["session_id"])
        else: # エラー時
            flash("エラーが発生しました", "failed")
            return redirect("/")

        # 該当するデータベースがない場合
        if not databases:
            flash("データベースを登録してください", "failed")
            return render_template("dbregister.html")

        # データベースidと合致するテーブルを取得
        for database in databases:
            rows = db.execute("SELECT * FROM tables WHERE database_id = ?", database["id"])
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
            table1 = db.execute("SELECT * FROM ?", table1_id)
            table1_columns = db.execute("SELECT * FROM columns WHERE table_id = ?", table1["id"])
        else: # テーブルが選択されていない時
            return render_template("dblist.html", databases=databases, tables=tables)
        if table2_id: # テーブル2が選択されている時
            table2 = db.execute("SELECT * FROM ?", table2_id)
            table2_columns = db.execute("SELECT * FROM columns WHERE table_id = ?", table2["id"])
        else: # テーブル1のみが選択されている時
            return render_template("dblist.html", databases=databases, tables=tables, table1_id=table1_id, table1=table1, table1_columns=table1_columns)
        if table3_id: # テーブル3が選択されている時
            table3 = db.execute("SELECT * FROM ?", table3_id)
            table3_columns = db.execute("SELECT * FROM columns WHERE table_id = ?", table3["id"])
            return render_template("dblist.html", databases=databases, tables=tables, table1_id=table1_id, table1=table1, table1_columns=table1_columns, table2_id=table2_id, table2=table2, table2_columns=table2_columns, table3_id=table3_id, table3=table3, table3_columns=table3_columns)
        else: # テーブル1とテーブル2のみが選択されている時
            return render_template("dblist.html", databases=databases, tables=tables, table1_id=table1_id, table1=table1, table1_columns=table1_columns, table2_id=table2_id, table2=table2, table2_columns=table2_columns)


