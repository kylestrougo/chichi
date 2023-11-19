from app import app, db
from flask import render_template, flash, redirect, url_for, request
from helper import scrape_data, update_player_by_tier
from app.models import User, Post
from app.forms import LoginForm, PostForm, PlayerSelectionForm, PlayerSelectionSubForm
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlsplit
from app.forms import RegistrationForm, EditProfileForm
from datetime import datetime
from app.models import Masters, updated, Draft
import pandas as pd
from wtforms.validators import InputRequired
from wtforms import BooleanField


@app.route('/')
@app.route('/index')
@login_required
def index():
    ##data = scrape_data()
    data = Masters.query.all()
    # print(data)

    # table_html = data.to_html(classes='table table-bordered', index=False)
    datetime = updated.query.all()

    return render_template('index.html', title='Home', data=data, datetime=datetime)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()

    return render_template('user.html', user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@app.route('/leaderboard')
@login_required
def leaderboard():
    # data = scrape_data()
    # table_html = data.to_html(classes='table table-bordered', index=False)
    return render_template('leaderboard.html')


@app.route('/smack', methods=['GET', 'POST'])
@login_required
def smack():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your shit talk is now live')
        return redirect(url_for('smack'))

    posts = Post.query.order_by(Post.timestamp.desc()).all()

    return render_template("smack.html", title='Smack Board', form=form,
                           posts=posts)



@app.route('/draft/<int:tier>/<username>', methods=['GET', 'POST'])
@login_required
def draft(tier, username):
    # Load players data based on tier from CSV or database
    # Replace this line with your data loading logic
    players = pd.read_csv('app/players_tiered.csv')
    players.drop(columns=['Unnamed: 0'], inplace=True)

    # Filter players based on the current tier
    filtered_players = players[players['Tier'] == tier]

    form = PlayerSelectionForm()

    # Update choices for the radio field dynamically
    form.player_selection.choices = [(index, player['Golfer']) for index, player in filtered_players.iterrows()]

    if form.validate_on_submit():
        selected_player_index = form.player_selection.data
        #selected_player = filtered_players.iloc[selected_player_index]
        selected_player = filtered_players.at[selected_player_index, 'Golfer']

        # Save selected player to the database or perform any other actions
        print(selected_player, " ", username)
        update_player_by_tier(username, tier, selected_player)

        # Redirect to the next tier or a different page
        next_tier = tier + 1
        if next_tier <= 6:
            return redirect(url_for('draft', tier=next_tier, username = username))
        else:
            # Draft completed, redirect to a different page
            username = User.query.filter_by(username=username).first_or_404()
            return redirect(url_for('user', username=username))

    return render_template('draft.html', title='Draft Lineup', form=form, players=filtered_players, tier=tier, username = username)