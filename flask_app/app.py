from flask import Flask, render_template, request, flash, url_for, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import URL, select
from sqlalchemy.exc import IntegrityError
from config import load_config
from models.models import *
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from forms import Login_form, Register_form, Create_Post_Form

cfg = load_config()

url = URL.create(
    drivername='postgresql+psycopg2',
    username=cfg.db.user,
    password=cfg.db.password,
    host=cfg.db.host,
    port=cfg.db.port,
    database=cfg.db.database
).render_as_string(hide_password=False)


app = Flask(__name__)

app.secret_key = cfg.flask.secret_key
app.config["SQLALCHEMY_DATABASE_URI"] = url
db = SQLAlchemy(app)
login_manager = LoginManager(app)

class Userlogin():
    def init_user_by_username(self, username, db: SQLAlchemy):
        self.__user = db.session.execute(select(User).where(User.username == username)).scalar()
        print(self.__user)
        return self

    def init_user_by_id(self, id, db: SQLAlchemy):
        self.__user = db.session.execute(select(User).where(User.id == id)).scalar()
        return self

    def init_user(self, user: User):
        self.__user = user
        return self

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.__user.email_verified

    def is_anonymous(self):
        return False

    def get_user(self) -> User:
        return self.__user

    def get_id(self):
        return self.__user.id

@login_manager.user_loader
def load_user(user_id):
    return Userlogin().init_user_by_id(user_id, db=db)

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template('index.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    login_form: Login_form = Login_form()
    if login_form.validate_on_submit():
        login = login_form.username.data
        password = login_form.password.data

        user = db.session.execute(select(User).where(User.username == login)).scalar()
        if not user or not check_password_hash(user.password ,password):
            flash("Неправильний логін або пароль")
        else:
            login_user(Userlogin().init_user(user))
            return redirect(url_for('profile', username=login))

    return render_template("login.html", form=login_form)
@app.route("/signup", methods=["GET", "POST"])
def signup():
    register_form: Register_form = Register_form()
    if register_form.validate_on_submit():
        login = register_form.username.data
        password = register_form.password.data
        rep_password = register_form.password_rep.data
        if password != rep_password:
            flash("Паролі не співпадають!")

        hash_password = generate_password_hash(password, method="sha256")
        user = User(username=login, password=hash_password, email_verified=False)
        try:
            db.session.add(user)
            db.session.commit()
        except (IntegrityError, Exception):
            db.session.rollback()
            flash(f"Користувач з іменем {login} вже існує")
        return render_template("index.html")
    else:
        for element, errors in register_form.errors.items():
            for error in errors:
                flash(error)


    return render_template("signup.html", form=register_form)

@app.route("/notes", methods=["GET", "POST"])
def show_notes():
    notes = db.session.execute(select(Note).where(Note.author == current_user.get_user()).order_by(Note.id)).scalars()
    return render_template("notes.html", notes=notes)


@app.route("/add_note")
def add_note():
    content = request.args.get("content")
    note = Note(content=content, author_id=current_user.get_user().id)
    db.session.add(note)
    db.session.commit()
    return redirect(url_for("show_notes"))

@app.route("/delete_note")
def delete_note():
    note_id = request.args.get("note_id")
    note = db.session.execute(select(Note).where(Note.id == note_id)).scalar()
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for("show_notes"))

@app.route("/mark_note", methods=["POST", "GET"])
def mark_note():
    note_id = int(request.json["note_id"])
    marked_as_done = request.json["checked"]
    note = db.session.execute(select(Note).where(Note.id == note_id)).scalar()
    note.mark_as_done = marked_as_done
    db.session.commit()
    return "Ok"


@app.route("/profile<username>")
@login_required
def profile(username):
    if not current_user.is_active():
        return redirect(url_for("verify", username=username))
    return redirect(url_for("show_notes"))


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/verify<username>")
@login_required
def verify(username):
    user: User = current_user.get_user()
    if user.email_verified:
        return redirect(url_for("profile", username=username))
    else:
        return render_template("verify.html", username=username)



@app.route("/verify", methods=["POST"])
def confirm():
    username = request.json["username"]
    user = db.session.execute(select(User).where(User.username == username)).scalar()
    user.email_verified = True
    db.session.commit()
    return jsonify(redirect_url=url_for("profile", username=username))

@app.errorhandler(404)
def page_not_found(exc):
    return ''

if __name__ == "__main__":
    app.run(debug=True)

