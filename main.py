from flask import Flask, render_template, redirect, url_for, flash, abort, request
from werkzeug import security
from werkzeug.security import check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user

from forms import RegisterUserForm, LoginUserForm
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sendlinks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    socials = db.relationship('Social', back_populates='user')  # parent table of Post


class Social(db.Model):
    social = db.Column(db.String(100), nullable=True, primary_key=True)
    link = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)  # foreign key of parent User

    user = db.relationship('User', back_populates='socials')


db.drop_all()
db.create_all()



@app.route('/')
def get_all_users():
    # print(f'current users id: {current_user.get_id()}')
    # print(f'current users type: {type(current_user.get_id())}')

    users = User.query.limit(10).all()
    return render_template("index.html", users=users)


@app.route('/register', methods=["POST", "GET"])
def register():
    if request.method == 'POST':
        user = User.query.filter_by(name=request.form['email']).first()
        if user:
            flash('User Already Exists, Please Login!')
            return redirect(url_for('login'))
        else:
            hashed_pass = security.generate_password_hash(request.form['pass'], method='pbkdf2:sha256', salt_length=8)
            new_user = User(
                name=request.form['name'],
                email=request.form['email'],
                password=hashed_pass
            )
            db.session.add(new_user)
            db.session.commit()



            user = User.query.filter_by(email=request.form['email']).first()
            login_user(user)

            return redirect(url_for('link_socials', id=user.id))

    return render_template("register.html")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def user_name(user_id):
    return User.query.get(user_id).name


@app.route('/login', methods=["POST", "GET"])
def login():
    form = LoginUserForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('link_socials', id=user.id))
    return render_template("login.html", form=form)


@app.route('/user/<id>', methods=["GET"])
def link_socials(id):
    user_profile = User.query.get(id)
    try:
        edit_option = False
        if int(current_user.get_id()) == int(id):
            edit_option = True

        return render_template('user.html', user_profile=user_profile, edit_option=edit_option)
    except:
        return render_template('404.html'), 404


@app.route('/user/<id>/edit', methods=["GET", "POST"])
@login_required
def add_socials(id):
    user_profile = User.query.get(id)
    if not user_profile:
        return render_template('404.html'), 404
    if request.method == "POST":
        list_of_links = {
            "profile_picture": request.form['profile_picture'],
            "twitter": request.form['twitter'],
            "instagram": request.form['instagram'],
            "facebook": request.form['facebook'],
            "linkedin": request.form['linkedin'],
            "youtube": request.form['youtube'],
            "others": request.form['others']
        }

        for key, value in list_of_links.items():
            print(key, value)
            if value != "":
                try:
                    if key == 'instagram':
                        links = Social(
                            social=key,
                            link=f'https://www.instagram.com/{value}',
                            user_id=int(current_user.get_id())
                        )
                        db.session.add(links)
                        db.session.commit()
                    elif key == 'twitter':
                        links = Social(
                            social=key,
                            link=f'https://www.twitter.com/{value}',
                            user_id=int(current_user.get_id())
                        )
                        db.session.add(links)
                        db.session.commit()
                    else:
                        links = Social(
                            social=key,
                            link=value,
                            user_id=int(current_user.get_id())
                        )
                        db.session.add(links)
                        db.session.commit()

                except:
                    db.session.rollback()
                    print(key)
                    print('Exception called!')
                    social_med = Social.query.filter_by(social=key, user_id=current_user.get_id()).first()
                    if key == 'instagram':
                        social_med.link = f'https://www.instagram.com/{value}'
                    elif key == 'twitter':
                        social_med.link = f'https://www.twitter.com/{value}'
                    else:
                        social_med.link = value
                    db.session.commit()

        return redirect(url_for('link_socials', id=current_user.get_id()))
    return render_template('edit.html', name=id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_users'))

@app.route('/<blah>')
def random(blah):
    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run(debug=True)
