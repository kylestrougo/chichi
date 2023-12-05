import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from flask_mail import Message
from app import mail
from flask import url_for
from flask_login import current_user
from app import db, app
from app.models import User, Masters, updated, Draft
from sqlalchemy.exc import IntegrityError
from flask import render_template
from threading import Thread


def scrape_data():
    # Replace 'url' with the URL of the webpage containing the table
    url = 'https://www.pgatour.com/tournaments/2024/masters-tournament/R2024014/past-results'
    response = requests.get(url)

    print("HTTP Response Status Code:", response.status_code)

    soup = BeautifulSoup(response.content, 'html.parser')

    # Print the first 200 characters of the HTML to check if it's what you expect
    # print("HTML Content (first 200 characters):", soup.prettify()[:200])

    table = soup.find('table', class_='chakra-table')

    # Check if the table was found
    # if table:
    #   print("**** Table found")

    data = []
    headers = []

    for row in table.find_all('tr'):
        cols = row.find_all(['th', 'td'])
        if not headers:
            headers = [header.text.strip() for header in cols]
        else:
            row_data = [col.text.strip() for col in cols]
            data.append(row_data)

    # Print the headers and a sample row to verify the data
    # print("Headers:", headers)
    # if data:
    #   print("Sample Row:", data[0])

    df = pd.DataFrame(data, columns=headers)

    df.drop(columns=['FedExCup Pts', 'Official Money'], inplace=True)
    df['Index'] = df.index
    df.set_index('Index', inplace=True)

    return df


def update_data():
    scraped_data = scrape_data()  # Scrape data from the website
    # Delete existing data
    app.app_context().push()
    db.session.query(Masters).delete()
    # Save the new data
    for index, row in scraped_data.iterrows():
        entry = Masters(
            pos=str(row['Pos']),
            player=row['Player'],
            r1=str(row['R1']),
            r2=str(row['R2']),
            r3=str(row['R3']),
            r4=str(row['R4']),
            to_par=str(row['To Par'])
        )
        db.session.add(entry)

    db.session.commit()

    d = datetime.now()
    d = d.strftime("%A, %b %d at %I:%M %p")
    d = "Refreshed: " + d
    # print(d)

    db.session.query(updated).delete()
    d = updated(datetime=str(d))
    db.session.add(d)

    db.session.commit()


def update_player_by_tier(user_id, tier, player_name):
    user_record = Draft.query.filter_by(user_id=user_id).first()

    if user_record:
        # Update existing record for the user and tier
        setattr(user_record, f'tier{tier}', player_name)
    else:
        # Create a new record if one doesn't exist for the user and tier
        user_record = Draft(user_id=user_id)
        setattr(user_record, f'tier{tier}', player_name)

    # Commit changes to the database
    try:
        db.session.add(user_record)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()  # Handle any errors that occurred during commit


def get_leaderboard():
    leaderboard_data = db.session.query(User.username, Draft, db.func.sum(Masters.to_par).label('total_score')) \
        .join(Draft) \
        .join(Masters, (Draft.tier1 == Masters.player) |
              (Draft.tier2 == Masters.player) |
              (Draft.tier3 == Masters.player) |
              (Draft.tier4 == Masters.player) |
              (Draft.tier5 == Masters.player) |
              (Draft.tier6 == Masters.player)) \
        .group_by(Draft.id) \
        .order_by('total_score') \
        .all()

    leaderboard_entries = []
    for entry in leaderboard_data:
        user_profile_url = url_for('user', username=entry.username)
        user_entry = f"<tr><td><a href='{user_profile_url}'>{entry.username}</a></td><td>{entry.Draft.tier1}</td><td>{entry.Draft.tier2}</td><td>{entry.Draft.tier3}</td><td>{entry.Draft.tier4}</td><td>{entry.Draft.tier5}</td><td>{entry.Draft.tier6}</td><td>{entry.total_score}</td></tr>"
        leaderboard_entries.append(user_entry)

    return leaderboard_entries


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('[Chi Chi] Reset Your Password',
               sender=app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)
