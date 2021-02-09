from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
import os, pymongo


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['plotting']=False


login_manager = LoginManager()
login_manager.init_app(app)

#Database
client = pymongo.MongoClient(os.getenv('DATABASE'))
db = client.user_login


## Define flask-login User class ## 
class User(UserMixin):
    def __init__(self, username):
        self.username = username

    def get_id(self):
        return self.username

    @staticmethod
    def check_password(password_entered, password):
        if password_entered == password:
            return True
        return False

    @login_manager.user_loader
    def load_user(username):
        user = db.users.find_one({"username": username})
        if user is None:
            return None
        return User(username=user['username'])


## Login/Register page
@app.route("/")
def login():
	return render_template("login.html")


@app.route("/", methods = ["POST"])
def login_or_register():
    if request.method == 'POST':
        name_entered = request.form.get('user_name') # Get username and password from form
        pw_entered = request.form.get('user_pw')

        if request.form.get('login'): # Log in logic
            user = db.users.find_one({'username':name_entered})
            if user and User.check_password(user['password'],pw_entered):
                usr_obj = User(username=user['username'])
                login_user(usr_obj)
                return redirect(url_for('main'))
            else:
                flash("Incorrect username and password combination") 
                return redirect(url_for('login'))

        elif request.form.get('register'): # Register logic
            new_user = {'username':name_entered,'password':pw_entered}
            db.users.insert_one(new_user) # insert new user to db
            return redirect(url_for('login')) # redirect after register


# Page where user logs sleep
@app.route("/main")
def main():
    user_data = db.users.find_one({'username':current_user.get_id()})
    return render_template("main.html",user=user_data,plot=app.config['plotting'])


# Function for adding sleep data
def add_sleep(time,date,user):
    if 'date' in user:
        user['date'].append(date)
        user['time'].append(time)
    else: # If first time adding sleep data
        user['date'] = [date]
        user['time'] = [time]

    # Update MongoDB Atlas
    db.users.update_one({'username':user['username']},
        {'$set':{'date':user['date'],
        'time':user['time']}})


@app.route('/main', methods=['POST','GET'])
def submit_sleep():
    if request.method == 'POST':

        if request.form.get('submit'): # if submitting new sleep data
            time_entered = float(request.form.get('time'))
            date_entered = request.form.get('date')
            add_sleep(time_entered,date_entered,db.users.find_one({'username':current_user.get_id()}))

        if request.form.get('logout'):
            logout_user()
            app.config['plotting'] = False
            return 'You logged out!'

        else: # If user has clicked "view graph", set plotting = True, redirect to '/main'
            app.config['plotting'] = True

    return redirect(url_for('main'))
    

if __name__ == "__main__":
	app.run(debug=True)
