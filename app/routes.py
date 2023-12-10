from app import app, db
from flask import render_template, flash, redirect, url_for, request
from helper import update_player_by_tier, get_leaderboard, send_password_reset_email
from app.models import User, Post
from app.forms import LoginForm, PostForm, PlayerSelectionForm, ResetPasswordRequestForm, ResetPasswordForm
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlsplit
from app.forms import RegistrationForm, EditProfileForm, TieBreakerForm
from datetime import datetime
from app.models import Masters, updated, Draft
import pandas as pd

trigger = 0

# Function to grant/ revoke access upon tournament start
def tournament_start():
    global trigger
    trigger = 1
    print("Access granted at:", datetime.now())

@app.route('/')
@app.route('/index')
@login_required
def index():
    data = Masters.query.all()
    for entry in data:
        if entry.pos not in ("CUT","W/D"):
            # Replace '0' with 'E' for r1, r2, r3, r4 for active player's scores
            entry.r1 = 'E' if entry.r1 == '0' else entry.r1
            entry.r2 = 'E' if entry.r2 == '0' else entry.r2
            entry.r3 = 'E' if entry.r3 == '0' else entry.r3
            entry.r4 = 'E' if entry.r4 == '0' else entry.r4

    datetime = updated.query.all()
    return render_template('index.html', title='Home', data=data, datetime=datetime)


@app.route('/user/<username>')
@login_required
def user(username):
    global trigger
    user = User.query.filter_by(username=username).first_or_404()
    user_record = Draft.query.filter_by(user=user).first()
    user_record_dict = {
        # "user_id": user_record.user_id,
        "tier1": user_record.tier1,
        "tier2": user_record.tier2,
        "tier3": user_record.tier3,
        "tier4": user_record.tier4,
        "tier5": user_record.tier5,
        "tier6": user_record.tier6
    }

    return render_template('user.html', user=user, user_record_dict=user_record_dict, user_record=user_record, trigger=trigger)


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
        login_user(user)
        return redirect(url_for('draft', tier=1, username=user))
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
    global trigger
    if trigger  == 1:
        leaderboard, x = get_leaderboard()
        return render_template('leaderboard.html', leaderboard=leaderboard)
    else:
        flash("Access to this page is granted upon Tournament Start")
        return redirect(url_for('index'))


@app.route('/smack', methods=['GET', 'POST'])
@login_required
def smack():
    global trigger
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your shit talk is now live')
        return redirect(url_for('smack'))

    posts = Post.query.order_by(Post.timestamp.desc()).all()

    return render_template("smack.html", title='Smack Board', form=form,
                           posts=posts, trigger=trigger)


@app.route('/draft/<int:tier>/<username>', methods=['GET', 'POST'])
@login_required
def draft(tier, username):
    players = pd.read_csv('app/players_tiered.csv')
    players.drop(columns=['Unnamed: 0'], inplace=True)

    # Filter players based on the current tier
    filtered_players = players[players['Tier'] == tier]

    form = PlayerSelectionForm()
    # Update choices for the radio field dynamically
    form.player_selection.choices = [(index, player['Golfer']) for index, player in filtered_players.iterrows()]
    user = User.query.filter_by(username=username).first_or_404()

    if form.validate_on_submit():
        selected_player_index = form.player_selection.data
        # selected_player = filtered_players.iloc[selected_player_index]
        selected_player = filtered_players.at[selected_player_index, 'Golfer']
        # Save selected player to the database or perform any other actions

        update_player_by_tier(user.id, tier, selected_player)

        # Redirect to the next tier or a different page
        next_tier = tier + 1
        if next_tier <= 6:
            return redirect(url_for('draft', tier=next_tier, username=user))
        else:
            # Draft completed, redirect to completed profile
            return redirect(url_for('tie_breaker', username=user))

    return render_template('draft.html', title='Draft Lineup', form=form, players=filtered_players, tier=tier,
                           username=user)


@app.route('/tier/<int:tier>/<username>', methods=['GET', 'POST'])
@login_required
def tier(tier, username):
    players = pd.read_csv('app/players_tiered.csv')
    players.drop(columns=['Unnamed: 0'], inplace=True)

    # Filter players based on the current tier
    filtered_players = players[players['Tier'] == tier]

    form = PlayerSelectionForm()
    # Update choices for the radio field dynamically
    form.player_selection.choices = [(index, player['Golfer']) for index, player in filtered_players.iterrows()]
    user = User.query.filter_by(username=username).first_or_404()

    if form.validate_on_submit():
        selected_player_index = form.player_selection.data
        # selected_player = filtered_players.iloc[selected_player_index]
        selected_player = filtered_players.at[selected_player_index, 'Golfer']
        # Save selected player to the database or perform any other actions

        update_player_by_tier(user.id, tier, selected_player)

        return redirect(url_for('user', username=current_user))

    return render_template('draft.html', title='Draft Lineup', form=form, players=filtered_players, tier=tier,
                           username=current_user)


@app.route('/tie_breaker/<username>', methods=['GET', 'POST'])
@login_required
def tie_breaker(username):
    form = TieBreakerForm()
    if form.validate_on_submit():
        user_draft = Draft.query.filter_by(user_id=current_user.id).first()
        if user_draft is None:
            user_draft = Draft(user_id=current_user.id)

        user_draft.single_number = form.single_number.data
        setattr(user_draft, f'single_number{form.single_number.data}', form.single_number.data)

        db.session.add(user_draft)
        db.session.commit()
        return redirect(url_for('user', username=current_user))

    return render_template('tie_breaker.html', form=form, username=current_user)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(db.select(User).where(User.email == form.email.data))
        # user = db.session.query(User).filter(User.email == form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)
