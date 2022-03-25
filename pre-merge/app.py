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

from werkzeug.security import check_password_hash, generate_password_hash

from tempfile import mkdtemp


app = Flask(__name__)
app.secret_key = 'abcdefghijklmn'

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["TEMPLATES_AUTO_RELOAD"] = True
Session(app)


connection = psycopg2.connect(host="localhost", database="Sample", user="postgres", password="724817tf", port=5432)
connection.autocommit = False
cur = connection.cursor()



# DATABASE = "postgresql+psycopg2://postgres:724817tf@localhost:5432/testDB"

# engine = sqlalchemy.create_engine(
#     DATABASE,
#     encoding="utf-8",
#     echo=True
# )

# # app.config.from_object('testDB.config.Config')

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

# https://shigeblog221.com/flask-session/
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("name"):
            return render_template("error.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("error.html")

        # Query database for username
        cur.execute("SELECT * FROM users WHERE name = %s;",
                          (request.form.get("name"),))
        for i in cur:
            if len(i) != 4 or not check_password_hash(i[3], request.form.get("password")):
                print("error hash")
                # cur.fetchall()
                # cur.close()
                # connection.close()
                return render_template("error.html")
            else:
                # cur.fetchall()
                # cur.close()
                # connection.close()
                session["user_id"] = i[0]
                return redirect("/")
        # Remember which user has logged in
        return render_template("error.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


def index():
    session.get('session_id', 1)
    return render_template("home.html")

@app.route("/error")
# @login_required
def error():
    return render_template("error.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # GETリクエストなら、登録画面を表示する
    if request.method == "GET":
        return render_template("register.html")

    # POSTリクエストなら、usernameやpasswordの情報が送られているということ。
    # よってデータベースにusername, address, passwordを追加する
    if request.method == "POST":
        # まずusernameとpasswordが入力されているか確かめる。
        if not request.form.get("name"):
            flash("『ユーザー名』に入力してください","failed")
            return redirect("/register")
        elif not request.form.get("address"):
            flash("『メールアドレス』に入力してください","failed")
            return render_template("register.html")
        elif not request.form.get("password"):
            flash("『パスワード』に入力してください","failed")
            return render_template("register.html")

        elif not request.form.get("confirmation"):
            flash("『パスワード確認』に入力してください","failed")
            return render_template("register.html")

        elif request.form.get("confirmation") != request.form.get("password"):
            flash("1回目と2回目のパスワードが違います","failed")
            return render_template("register.html")

        else:
            cur.execute("SELECT * FROM users;")
            # for i in cur:
            #     print(i)
            cur.execute("INSERT INTO users (name, address, hash) VALUES (%s, %s, %s);",
                       (request.form.get("name"), request.form.get("address"), generate_password_hash(request.form.get("password"), method='sha256')))

            flash("登録しました","success")
            cur.execute("select * from users where name = 'd'")
            app.logger.debug(cur.fetchall())
            return redirect("/login")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

# @app.route("/sqllist")
# def sqllist():
#   databases = Database.query.all()
#   tables = Table.query.all()
#   return render_template("sqllist.html", databases=databases, tabales=tables)


@app.route("/dbregister", methods=['GET', 'POST'])
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

    # return redirect(url_for('dblist', table1_id=table_ids[0]))
    return redirect("/dblist")

  else:
    return render_template("dbregister.html")

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
        # return render_template("dblist.html")
        session["user_id"] = 1
        # データベースを取得
        try:
            user_id = session["user_id"] # ログイン時
            cur.execute("SELECT * FROM databases WHERE user_id = %s;", (user_id,))
            databases = cur.fetchall()
        except:
            try:
                id = session.get("session_id") # 未ログイン時
                cur.execute("SELECT * FROM databases WHERE session_id = %s;", (id))
                databases = cur.fetchall()
            except: # エラー時
                flash("エラーが発生しました", "failed")
                #return redirect("/")

        # 該当するデータベースがない場合
        if not databases:
            flash("データベースを登録してください", "failed")
            return render_template("dbregister.html")

        # データベースidと合致するテーブルを取得
        tables = []
        for database in databases:
            cur.execute("SELECT * FROM tables WHERE database_id = %s;", (database[0],))
            rows = cur.fetchall()
            tables.extend(rows)

        # 画面右側に表示するテーブル
        table1_id = request.args.get("table1_id")
        table2_id = request.args.get("table2_id")
        table3_id = request.args.get("table3_id")

        # 画面遷移
        if table1_id: # テーブル1が選択されている時
            try:
                cur.execute("SELECT name FROM tables WHERE id = %s;", table1_id)
            except:
                flash("エラーが発生しました", "failed")
                return redirect("/")
            table1_names = cur.fetchall()
            table1_name = table1_names[0][0]
            cur.execute("SELECT * FROM harry_potter;")#, (table1_name,))
            table1 = cur.fetchall()
            table1_columns = [col.name for col in cur.description]
        else: # テーブルが選択されていない時
            return render_template("dblist.html", databases=databases, tables=tables)
        if table2_id: # テーブル2が選択されている時
            try:
                table2_name = cur.execute("SELECT name FROM tables WHERE id = %s;", table2_id)[0]["name"]
            except:
                flash("エラーが発生しました", "failed")
                return redirect("/")
            cur.execute("SELECT * FROM (%s);", table2_name)
            table2 = cur.fetchall()
            table2_columns = [col.name for col in cur.description]
        else: # テーブル1のみが選択されている時
            return render_template("dblist.html", databases=databases, tables=tables, table1_id=table1_id, table1=table1, table1_columns=table1_columns, table1_name=table1_name)
        if table3_id: # テーブル3が選択されている時
            try:
                table3_name = cur.execute("SELECT name FROM tables WHERE id = %s;", table3_id)[0]["name"]
            except:
                flash("エラーが発生しました", "failed")
                return redirect("/")
            cur.execute("SELECT * FROM %(s);", table3_name)
            table3 = cur.fetchall()
            table3_columns = [col.name for col in cur.description]

            #DBとの接続解除
            cur.close()
            connection.close()

            return render_template("dblist.html", databases=databases, tables=tables, table1_id=table1_id, table1=table1, table1_columns=table1_columns, table1_name=table1_name, table2_id=table2_id, table2=table2, table2_columns=table2_columns, table2_name=table2_name, table3_id=table3_id, table3=table3, table3_columns=table3_columns, table3_name=table3_name)

        else: # テーブル1とテーブル2のみが選択されている時
            return render_template("dblist.html", databases=databases, tables=tables, table1_id=table1_id, table1=table1, table1_columns=table1_columns, table1_name=table1_name, table2_id=table2_id, table2=table2, table2_columns=table2_columns, table2_name=table2_name)
