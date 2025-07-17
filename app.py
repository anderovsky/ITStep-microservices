from urllib import request

from flask import Flask, flash, redirect, render_template
from flask_login import LoginManager, login_required
from werkzeug.security import generate_password_hash

from models import *

app = Flask(__name__)
app.config['SECRET_KEY'] = 'most-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///microservices.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# routes
@app.route('/', methods=['GET', 'POST'])
def index():
    services = Review.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', services=services)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']

        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('login'))

        # create new user
        hashed_password = generate_password_hash(password)
        user = User(email=email, password=hashed_password, name=name)
        db.session.add(user)
        db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# create tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run()
