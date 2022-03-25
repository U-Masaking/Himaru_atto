from flask import Flask, flash, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker
import psycopg2


app = Flask(__name__)
app.secret_key = 'abcdefghijklmn'
#島崎のローカルのdatabaseに接続
connection = psycopg2.connect(host="localhost", database="mydb", user="postgres", password="0627", port=5432)
connection.autocommit = True
cur = connection.cursor()
cur.execute("select version()")
print(connection.get_backend_pid())

# SQLAlchemy の設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.py'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# @app.route("/")
# # @login_required
# def index():
#     return render_template("index.html")

# https://shigeblog221.com/flask-session/
@app.route("/")
def login_():

    if not session.get("user_id") and not session.get("session_id"):
        session_ids = cur.execute("SELECT * FROM preusers ORDER BY session_id DESC")
        if session_ids == None:
            session_id = 1
        else:
            session_id = int(session_ids[0]["session_id"]) + 1
        cur.execute("INSERT INTO preusers (session_id) VALUES(%i)", (int(session_id)))
        session.get('session_id', session_id)
        
        return render_template("login.html")


def index():
    session.get('session_id', 1)
    return render_template("index.html")

@app.route("/error")
# @login_required
def error():
    return render_template("error.html")

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


if __name__ == "__main__":
  app.run(debug=True)
