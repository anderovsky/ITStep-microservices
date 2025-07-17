from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Service, Review

app = Flask(__name__)
app.config['SECRET_KEY'] = 'velmi-tajny-kluc'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///microservices.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    services = Service.query.order_by(Service.created_at.desc()).all()
    return render_template('index.html', services=services)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']

        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))

        # Create new user
        hashed_password = generate_password_hash(password)
        user = User(email=email, password=hashed_password, name=name)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please login.')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))


@app.route('/add_service', methods=['GET', 'POST'])
@login_required
def add_service():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = float(request.form['price'])

        service = Service(
            title=title,
            description=description,
            price=price,
            user_id=current_user.id
        )
        db.session.add(service)
        db.session.commit()

        flash('Service added successfully!')
        return redirect(url_for('index'))

    return render_template('add_service.html')


@app.route('/service/<int:service_id>')
def service_detail(service_id):
    service = Service.query.get_or_404(service_id)
    reviews = Review.query.filter_by(service_id=service_id).order_by(Review.created_at.desc()).all()

    # Calculate average rating
    if reviews:
        avg_rating = sum(r.rating for r in reviews) / len(reviews)
    else:
        avg_rating = 0

    return render_template('service_detail.html',
                           service=service,
                           reviews=reviews,
                           avg_rating=avg_rating)


@app.route('/add_review/<int:service_id>', methods=['POST'])
@login_required
def add_review(service_id):
    service = Service.query.get_or_404(service_id)

    # Check if user is trying to review their own service
    if service.user_id == current_user.id:
        flash('You cannot review your own service!')
        return redirect(url_for('service_detail', service_id=service_id))

    # Check if user already reviewed this service
    existing_review = Review.query.filter_by(user_id=current_user.id, service_id=service_id).first()
    if existing_review:
        flash('You have already reviewed this service!')
        return redirect(url_for('service_detail', service_id=service_id))

    rating = int(request.form['rating'])
    comment = request.form.get('comment', '')

    review = Review(
        rating=rating,
        comment=comment,
        user_id=current_user.id,
        service_id=service_id
    )
    db.session.add(review)
    db.session.commit()

    flash('Review added successfully!')
    return redirect(url_for('service_detail', service_id=service_id))


# Create tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)