from flask import Flask,render_template,flash,redirect,url_for,session,request
from wtforms import Form,StringField,PasswordField,validators, SelectField, DateField
from passlib.hash import sha256_crypt
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

app.secret_key = "hamdiozdemir61"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/hamdiozdemir/Desktop/mindyourbusiness/isinebak.db'
db = SQLAlchemy(app)


class Userv2(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    surname = db.Column(db.String)
    username = db.Column(db.String)
    password = db.Column(db.String)
    department = db.Column(db.String)

class TodoV2(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    content = db.Column(db.String)
    complete = db.Column(db.Boolean)
    archive = db.Column(db.Boolean)
    who = db.Column(db.String)
    responsible = db.Column(db.String)
    last_date = db.Column(db.Date)

class LoginForm(Form):
    username = StringField("Username",validators=[validators.Length(min=3)])
    password = PasswordField("Password?")

class RegisterForm(Form):
    name = StringField("Name")
    surname = StringField("Surname")
    username = StringField("Username", validators=[validators.DataRequired(message="It would be great if you give us a username"),validators.Length(min=3,max=25)])
    password = PasswordField("Password", validators=[validators.DataRequired(message="Everybody needs a password."), validators.Length(min=6)])
    department = SelectField(u"Select Your Department",choices=[("Admin"),("Department 1"),("Department 2"),("Department 3"),("Department 4")], validators=[validators.DataRequired(message="Please choose where you belong, else everybody gives you everyjob. Be smart!")])

class TodoForm(Form):
    deadline = DateField("Deadline",format='%Y-%m-%d',validators=[validators.DataRequired(message="It should be finished one day, right?")])

# login_required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if "logged_in" in session:
            return f(*args,**kwargs)
        else:
            flash("Login First, View Then !","danger")
            return redirect(url_for("login"))
    return decorated_function


@app.route("/",methods=["GET","POST"])
def index():
    today = datetime.now().date()
    departmentsAll = ["Department 1","Department 2","Department 3","Department 4"]
    if "logged_in" in session:
        form = TodoForm(request.form)

        if session["department"] == "Admin":
            todos = TodoV2.query.filter_by(archive=False)
            users = Userv2.query.order_by(Userv2.name).all()
            return render_template("index.html",todos=todos,today=today,form=form,departmentsAll=departmentsAll,users=users)

        else:
            todo1 = TodoV2.query.filter_by(responsible=session["department"],archive=False)
            todo2 = TodoV2.query.filter_by(responsible="Common",archive=False).union(TodoV2.query.filter_by(responsible=session["name"],archive=False))
            todos= todo1.union(todo2)
            return render_template("index.html",todos=todos,today=today,form=form,departmentsAll=departmentsAll)

    else:
        return render_template("index.html")

# Login page
@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm(request.form)

    if request.method == "POST":
        username_entered = form.username.data
        password_entered = form.password.data

        global user 
        user = Userv2.query.filter_by(username=username_entered).first()
        if user == None:
            flash("Incorrect username. Are you sure you're working with us?","danger")
            redirect(url_for("login"))
        else:
            real_password = user.password
            if sha256_crypt.verify(password_entered,real_password):
                session["logged_in"] = True
                session["username"] = user.username
                session["name"] = user.name
                session["department"] = user.department
                flash("Welcome. You have successfuly entered slavey system","success")
                return redirect(url_for("index"))
            else:
                flash("Incorrect password! Sorry, we don't have 'Forget Password' section.","danger")
                redirect(url_for("login"))
    else:
        redirect(url_for("login"))

    return render_template("login.html",form=form)

#Register
@app.route("/register", methods=["GET","POST"])
def register():
    search = Userv2.query.filter_by(username="Zehra").first()
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        surname = form.surname.data
        username = form.username.data
        password = sha256_crypt.encrypt(form.password.data)
        department = form.department.data

        # "isAvailable" function checks whether username entered is already taken or not.
        if isAvailable(username) == False:
            flash("This username has already taken. You can 'michaeljordan_61' or something like this","danger")
            return redirect(url_for("register"))
        else:
            newUser = Userv2(name=name,surname=surname,username=username,password=password,department=department)
            db.session.add(newUser)
            db.session.commit()
            flash("Welcome! Give me a hug!","success")
            return redirect(url_for("login"))      
    else:
        return render_template("register.html", form=form,search=search)
   
#Logout
@app.route("/logout")
def logout():
    session.clear()
    flash("Where are you going? Is that end of the shift? ","warning")
    return redirect(url_for("index"))

#Add To-Do
@app.route("/add",methods=["POST"])
@login_required
def addtodo():
    form = TodoForm(request.form)

    title = request.form.get("title")
    content = request.form.get("content")
    responsible = request.form.get("responsible")
    deadline = form.deadline.data
    newTodo = TodoV2(title=title,content=content,complete=False,archive=False,who="",responsible=responsible,last_date=deadline)

    db.session.add(newTodo)
    db.session.commit()
    flash("Great, we have a new job!","success")
    return redirect(url_for("index"))

#Check/Comlete a To-Do
@app.route("/complete/<string:id>")
@login_required
def completeTodo(id):
    todo = TodoV2.query.filter_by(id=id).first()
    permissions = ["Common", session["name"],session["department"]]
    if todo.responsible in permissions or session["department"] == "Admin":
        todo = TodoV2.query.filter_by(id=id).first()
        todo.complete = not todo.complete
        db.session.commit()
        return redirect(url_for("index"))
    else:
        flash("This is not one of yours! Mind Your Business !","danger")
        return redirect(url_for("index"))

#Archive a To-Do
@app.route("/archive/<string:id>")
@login_required
def archiveTodo(id):
    todo = TodoV2.query.filter_by(id=id).first()
    permissions = ["Common", session["name"],session["department"]]
    if todo.responsible in permissions or session["department"] == "Admin":
        todo = TodoV2.query.filter_by(id=id).first()
        todo.archive = not todo.archive
        db.session.commit()
        flash("Now, another job is history.","secondary")
        return redirect(url_for("index"))
    else:
        flash("This is not one of yours! Mind Your Business !","danger")
        return redirect(url_for("index"))

#Undo From archive - send back to main
@app.route("/sendback/<string:id>")
@login_required
def sendBack(id):
    todo = TodoV2.query.filter_by(id=id).first()
    permissions = ["Common",session["name"],session["department"]]
    if todo.responsible in permissions or session["department"] == "Admin":
        todo = TodoV2.query.filter_by(id=id).first()
        todo.archive = not todo.archive
        db.session.commit()
        flash("Oh, great. We correct that mistake.","success")
        return redirect(url_for("viewarchive"))
    else:
        flash("This is not one of yours! Mind Your Business !","danger")
        return redirect(url_for("viewarchive"))


#View the archive
@app.route("/viewarchive")
@login_required
def viewarchive():
    
    # Admin can see everything
    if session["department"] == "Admin":
        archives = TodoV2.query.filter_by(archive=True)
    # Others can see the job from their departments, Common and assign to their names. I made there union to merge them.
    else:
        archives1 = TodoV2.query.filter_by(responsible=session["name"], archive=True)
        archives2 = TodoV2.query.filter_by(responsible="Common",archive=True).union(TodoV2.query.filter_by(responsible=session["department"], archive=True))
        archives = archives1.union(archives2)

    return render_template("viewarchive.html",archives=archives)

#Delete a To-do
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    todo = TodoV2.query.filter_by(id=id).first()
    permissions = ["Common",session["name"],session["department"]]
    if todo.responsible in permissions or session["department"] == "Admin":
        db.session.delete(todo)
        db.session.commit()
        flash("To-Do has been deleted successfuly. I hope you haven't made a mistake. Bcoz No-Way-Back!","success")
        return redirect(url_for("viewarchive"))
    else:
        flash("This is not one of yours! Mind Your Business !","danger")
        return redirect(url_for("viewarchive"))


#Checks the username if it is available at register step
def isAvailable(username_entered):
    if Userv2.query.filter_by(username=username_entered).first() == None:
        return True
    else:
        return False


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)