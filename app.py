from re import search
from flask import Flask, flash, render_template, session, request, redirect, url_for
from flask_session import Session
from testProject.database import init_db, db
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
import testProject.models
import psycopg2
import sqlalchemy
import re

from tempfile import mkdtemp


app = Flask(__name__)

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["TEMPLATES_AUTO_RELOAD"] = True
Session(app)


connection = psycopg2.connect(host="localhost", database="Sample", user="postgres", password="", port=5432)
connection.autocommit = False
cur = connection.cursor()



# DATABASE = "postgresql+psycopg2://postgres:724817tf@localhost:5432/Sample"

# engine = sqlalchemy.create_engine(
#     DATABASE,
#     encoding="utf-8",
#     echo=True
# )

# # app.config.from_object('Sample.config.Config')

# db = SQLAlchemy(app)

# session1 = scoped_session(
#     sessionmaker(
#         autocommit=False,
#         autoflush=False,
#         bind=engine
#     )
# )

# session = session1()

# db.create_all()


def search_highlight(query):

    words = re.split('[ ,()]', query)
    column = ''
    column2 = ''
    row = ''

    # select文のとき
    if words[0][0] == 's' or words[0][0] =='S':
        column = words[1]

        if len(words) >= 5:
            for i in range(len(words)):
                if words[i].lower() == 'where':
                    column2 = words[i + 1]
                    if words[i+3][0] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                        row = int(words[i+3])
                    else:
                        row = words[i+3]

    # updateのとき
    if words[0][0] == 'u' or words[0][0] == 'U':
        column = ''
        for i in range(len(words)):
            if words[i].lower() == 'where':
                column2 = words[i+1]
                if words[i+3][0] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                    row = int(words[i+3])
                else:
                    row = words[i+3]
    app.logger.debug(type(row))
    return column, column2, row


@app.route("/", methods=["GET", "POST"])
def home():
    # postのときの処理
    if request.method == "POST":

        # 値の取得とエラーチェック
        db_name = request.form.get("db_name")
        tb_name = request.form.get("table_name")

        cur.execute("SELECT name FROM databases")
        db_list = cur.fetchall()

        if db_name not in db_list[0]:
            flash("データベースが存在しません")
            return render_template("home.html")

        cur.execute("SELECT id FROM databases WHERE name = %(db_name)s", {'db_name':db_name})
        db_id = cur.fetchall()[0][0]

        cur.execute("SELECT name FROM tables WHERE database_id = %(db_id)s" % {'db_id':db_id})
        tb_list = cur.fetchall()

        if tb_name not in tb_list[0]:
            flash("テーブルが存在しません")
            return render_template("home.html")

        # templateが選択されたときのテーブルの複製
        if tb_name == "harry_potter":
            cur.execute("create table cp_template (like harry_potter including all)")
            cur.execute("insert into cp_template select * from harry_potter")
            cur.execute("insert into tables (name, database_id) values ('cp_template', 1)")
            tb_name = "cp_template"

        # 選択されたテーブルとデータベースの表示
        return redirect(url_for('index_before', db_id=db_id, table1_name=tb_name))

    # getのとき
    return render_template("home.html")


@app.route('/index_before/<int:db_id>/<string:table1_name>', methods=["GET", "POST"])
def index_before(db_id, table1_name):
    # userID = session["user_id"]
    transaction_flag = False

    cur.execute("SELECT * FROM %(name)s" % {'name':table1_name})
    table1 = cur.fetchall()

    # cur.execute("SELECT column_name AS name FROM information_schema.columns WHERE table_name = %(name)s" % {'name':table1_name})
    table1_columns = [col.name for col in cur.description]

    # postのとき
    if request.method == "POST":

        # 終了ボタンが押されたとき
        if request.form['send'] == 'end':

            if transaction_flag == True:
                cur.execute("ROLLBACK;")

            if table1_name == "cp_template":
                cur.execute("drop table if exists cp_template")

            return redirect(url_for('home'))

        query = request.form.get("Query")

        # 一時保存の場合
        if request.form['send'] == 'temporary':
            if transaction_flag == False:
                transaction_flag = True
                cur.execute("BEGIN;")

            try :
                cur.execute(query)
            except :
                flash("SQL構文が間違っています")
                return render_template("index_before.html", table1=table1, table1_columns=table1_columns, id=db_id, name=table1_name)

            # 入力がselect文のとき
            if query[0] == 's' or query[0] == 'S':

                # ユーザーが捜査した後のテーブル取得
                operated_table = cur.fetchall()

            # select文以外
            else:
                cur.execute("select * from %(name)s" % {'name':table1_name})
                operated_table = cur.fetchall()

            o_table_columns = [col.name for col in cur.description]

            # 全体テーブルでハイライトする部分の特定
            h_col, h_col2, h_row = search_highlight(query)

            app.logger.debug(h_col)
            app.logger.debug(h_col2)
            app.logger.debug(h_row)

            h_col_site, h_col2_site = 0, 0
            for i in range(len(table1_columns)):
                if h_col == table1_columns[i]:
                    h_col_site = i+1
                if h_col2 == table1_columns[i]:
                    h_col2_site = i+1

            app.logger.debug(h_col2_site)
            app.logger.debug(h_col_site)

            return render_template("index_before.html", table1=table1, table1_columns=table1_columns, operated_table=operated_table, o_table_columns=o_table_columns, id=db_id, name=table1_name, h_col=h_col, h_col2=h_col2, h_row=h_row, h_col_site=h_col_site, h_col2_site=h_col2_site)


        # 実行した場合
        if request.form['send'] == 'execute':
            try :
                cur.execute(query)
            except :
                flash("SQL構文が間違っています")
                return render_template("index_before.html", table1=table1, table1_columns=table1_columns, id=db_id, name=table1_name)

            # 入力がselect文のとき
            if query[0] == 's' or query[0] == 'S':
                operated_table = cur.fetchall()

            # select文以外
            else:
                cur.execute("select * from %(name)s" % {'name':table1_name})
                operated_table = cur.fetchall()

            o_table_columns = [col.name for col in cur.description]

            if transaction_flag == True:
                cur.execute("COMMIT;")

            flash("データベースが編集されました")

            # 全体テーブルでハイライトする部分の特定
            h_col, h_col2, h_row = search_highlight(query)

            h_col_site, h_col2_site = 0, 0
            for i in range(len(table1_columns)):
                if h_col == table1_columns[i]:
                    h_col_site = i+1
                if h_col2 == table1_columns[i]:
                    h_col2_site = i+1

            return render_template("index_before.html", table1=table1, table1_columns=table1_columns, operated_table=operated_table, o_table_columns=o_table_columns, id=db_id, name=table1_name, h_col=h_col, h_col2=h_col2, h_row=h_row, h_col_site=h_col_site, h_col2_site=h_col2_site)

    return render_template('index_before.html', table1=table1, table1_columns=table1_columns, id=db_id, name=table1_name)


@app.route("/index_after/<int:db_id>/<string:table1_name>", methods=["GET", "POST"])
def index_after(db_id, table1_name):
    # userID = session["user_id"]
    transaction_flag = False

    cur.execute("SELECT * FROM %(name)s" % {'name':table1_name})
    table1 = cur.fetchall()

    # cur.execute("SELECT column_name AS name FROM information_schema.columns WHERE table_name = %(name)s" % {'name':table1_name})
    table1_columns = [col.name for col in cur.description]

    # postのとき
    if request.method == "POST":

        # 終了ボタンが押されたとき
        if request.form['send'] == 'end':

            if transaction_flag == True:
                cur.execute("ROLLBACK;")

            if table1_name == "cp_template":
                cur.execute("drop table if exists cp_template")

            return redirect(url_for('home'))

        query = request.form.get("Query")

        # 一時保存の場合
        if request.form['send'] == 'temporary':
            if transaction_flag == False:
                transaction_flag = True
                cur.execute("BEGIN;")

            try :
                cur.execute(query)
            except :
                flash("SQL構文が間違っています")
                return render_template("index_before.html", table1=table1, table1_columns=table1_columns, id=db_id, name=table1_name)

            # 入力がselect文のとき
            if query[0] == 's' or query[0] == 'S':

                # ユーザーが捜査した後のテーブル取得
                operated_table = cur.fetchall()

            # select文以外
            else:
                cur.execute("select * from %(name)s" % {'name':table1_name})
                operated_table = cur.fetchall()

            o_table_columns = [col.name for col in cur.description]

            # 全体テーブルでハイライトする部分の特定
            h_col, h_col2, h_row = search_highlight(query)

            app.logger.debug(h_col)
            app.logger.debug(h_col2)
            app.logger.debug(h_row)

            h_col_site, h_col2_site = 0, 0
            for i in range(len(table1_columns)):
                if h_col == table1_columns[i]:
                    h_col_site = i+1
                if h_col2 == table1_columns[i]:
                    h_col2_site = i+1

            app.logger.debug(h_col2_site)
            app.logger.debug(h_col_site)

            return render_template("index_before.html", table1=table1, table1_columns=table1_columns, operated_table=operated_table, o_table_columns=o_table_columns, id=db_id, name=table1_name, h_col=h_col, h_col2=h_col2, h_row=h_row, h_col_site=h_col_site, h_col2_site=h_col2_site)


        # 実行した場合
        if request.form['send'] == 'execute':
            try :
                cur.execute(query)
            except :
                flash("SQL構文が間違っています")
                return render_template("index_before.html", table1=table1, table1_columns=table1_columns, id=db_id, name=table1_name)

            # 入力がselect文のとき
            if query[0] == 's' or query[0] == 'S':
                operated_table = cur.fetchall()

            # select文以外
            else:
                cur.execute("select * from %(name)s" % {'name':table1_name})
                operated_table = cur.fetchall()

            o_table_columns = [col.name for col in cur.description]

            if transaction_flag == True:
                cur.execute("COMMIT;")

            flash("データベースが編集されました")

            # 全体テーブルでハイライトする部分の特定
            h_col, h_col2, h_row = search_highlight(query)

            h_col_site, h_col2_site = 0, 0
            for i in range(len(table1_columns)):
                if h_col == table1_columns[i]:
                    h_col_site = i+1
                if h_col2 == table1_columns[i]:
                    h_col2_site = i+1

            return render_template("index_before.html", table1=table1, table1_columns=table1_columns, operated_table=operated_table, o_table_columns=o_table_columns, id=db_id, name=table1_name, h_col=h_col, h_col2=h_col2, h_row=h_row, h_col_site=h_col_site, h_col2_site=h_col2_site)

    return render_template('index_before.html', table1=table1, table1_columns=table1_columns, id=db_id, name=table1_name)
