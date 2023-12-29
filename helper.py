import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from flask_mail import Message
import re
from app import mail
from flask import url_for
from app import db, app
from app.models import User, Masters, updated, Draft
from sqlalchemy.exc import IntegrityError
from flask import render_template
from threading import Thread
from collections import defaultdict

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


    df = pd.DataFrame(data, columns=headers)

    # Your existing code for data cleaning and formatting
    df.drop(columns=['FedExCup Pts', 'Official Money'], inplace=True)
    df['Index'] = df.index
    df.set_index('Index', inplace=True)
    df['Player'] = df['Player'].str.replace('\(a\)', '', regex=True)
    df = df[df['Player'] != 'None']
    df = df.dropna(subset=['Player'], how='any')
    df = df[df['Player'].astype(str).str.strip() != '']  # Drop rows with empty strings in 'Player' column
    def is_non_numeric_or_blank(s):
        return not bool(re.match(r'^\+?-?\d*\.?\d*$', str(s)))

    columns_to_check = ['R1', 'R2', 'R3', 'R4', 'To Par']
    df[columns_to_check] = df[columns_to_check].fillna('0')

    for col in columns_to_check:
        df[col] = df[col].apply(lambda x: '0' if pd.isna(x) or is_non_numeric_or_blank(x) else x)

    # Updated section to handle empty strings and '-' cases
    for index, row in df.iterrows():
        for col in columns_to_check:
            val = row[col]
            if isinstance(val, str) and val.strip():  # Check for non-empty strings
                if val.startswith('+'):
                    val = int(val[1:])  # Convert to positive integer
                elif val.startswith('-') and val[1:]:  # Check for non-empty string after '-'
                    val = -int(val[1:])  # Convert to negative integer
                elif val.isdigit() or (val[1:].isdigit() and val[0] == '-'):
                    val = int(val)  # Convert to integer if it's a digit or negative digit

                # Update the value back to the DataFrame
                df.at[index, col] = val
            else:
                df.at[index, col] = 0  # Replace empty strings with 0

    return df

def masters_api():
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"

    querystring = {"orgId": "1", "tournId": "016", "year": "2022"}

    headers = {
        "X-RapidAPI-Key": "a0ad1bcf9amsh91cc2112fc6cc5bp10c0dajsne93b3dec7c82",
        "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    json_data = response.json()

    # Extracting the 'leaderboardRows' data
    leaderboard_data = json_data.get('leaderboardRows', [])

    # Function to cleanse score values
    def cleanse_score(score):
        if score == 'E':
            return 0
        elif score is None:
            return None
        else:
            return int(score)

    # Creating lists to hold extracted data
    player_data = []

    # Extracting required data elements from the leaderboard data
    for player in leaderboard_data:
        player_info = {
            'Pos': player.get('position'),
            'Player': player.get('firstName') + ' ' + player.get('lastName'),
            'playerId': player.get('playerId'),
            'R1': cleanse_score(next((round_data['scoreToPar'] for round_data in player['rounds'] if round_data['roundId']['$numberInt'] == '1'), None)),
            'R2': cleanse_score(next((round_data['scoreToPar'] for round_data in player['rounds'] if round_data['roundId']['$numberInt'] == '2'), None)),
            'R3': cleanse_score(next((round_data['scoreToPar'] for round_data in player['rounds'] if round_data['roundId']['$numberInt'] == '3'), None)),
            'R4': cleanse_score(next((round_data['scoreToPar'] for round_data in player['rounds'] if round_data['roundId']['$numberInt'] == '4'), None)),
            'To Par': cleanse_score(player.get('total'))
        }
        player_data.append(player_info)

    # Create DataFrame from extracted data
    player_df = pd.DataFrame(player_data)

    return player_df


def update_data():
    #scraped_data = scrape_data()  # Scrape data from the website
    scraped_data = masters_api() # fetch data from api
    # Delete existing data
    app.app_context().push()
    db.session.query(Masters).delete()

    # Save the new data with 'to_par' values as integers
    for index, row in scraped_data.iterrows():
        to_par = row['To Par']

        entry = Masters(
            pos=str(row['Pos']),
            player=row['Player'],
            playerId=row['playerId'],
            r1=str(row['R1']),
            r2=str(row['R2']),
            r3=str(row['R3']),
            r4=str(row['R4']),
            to_par=to_par  # Store the converted value as integer in the DB
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

'''
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
'''

def update_player_by_tier(user_id, tier, player_name, player_id):
    user_record = Draft.query.filter_by(user_id=user_id).first()
    player_id = int(player_id)

    if user_record:
        # Update existing record for the user and tier
        setattr(user_record, f'tier{tier}', player_name)
        setattr(user_record, f't{tier}_id', player_id)  # Update player ID for the tier
    else:
        # Create a new record if one doesn't exist for the user and tier
        user_record = Draft(user_id=user_id)
        setattr(user_record, f'tier{tier}', player_name)
        setattr(user_record, f't{tier}_id', player_id)  # Set player ID for the tier

    # Commit changes to the database
    try:
        db.session.add(user_record)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()  # Handle any errors that occurred during commit

def get_leaderboard():
    # Fetching leaderboard data
    leaderboard_data = db.session.query(User.username, Draft, db.func.sum(Masters.to_par).label('total_score')) \
        .join(Draft) \
        .join(Masters, (Draft.t1_id == Masters.playerId) |
              (Draft.t2_id == Masters.playerId) |
              (Draft.t3_id == Masters.playerId) |
              (Draft.t4_id == Masters.playerId) |
              (Draft.t5_id == Masters.playerId) |
              (Draft.t6_id == Masters.playerId)) \
        .group_by(Draft.id) \
        .all()

    # Collecting scores and users
    scores = defaultdict(list)
    for entry in leaderboard_data:
        total_score = entry.total_score
        predicted_score = entry.Draft.single_number
        top_player_to_par = Masters.query.order_by(Masters.pos).first().to_par  # Fetching top-ranked player's "To Par"
        score_difference = abs((top_player_to_par) - (predicted_score))

        score = (total_score, score_difference)
        scores[score].append(entry)

    # Sorting the scores
    sorted_scores = sorted(scores.keys(), key=lambda x: (x[0], x[1]))  # Sort by total_score and closest predicted score to top-ranked player's "To Par"
    leaderboard_entries = []
    leaderboard_email = []
    rank = 1
    for score in sorted_scores:
        for entry in scores[score]:
            user_profile_url = url_for('user', username=entry.username)
            user_entry = f"<tr><td>{rank}</td><td><a href='{user_profile_url}' style=\"color: blue; max-width: 200px; text-decoration: underline;\">{entry.username}</a></td><td>{entry.Draft.tier1}</td><td>{entry.Draft.tier2}</td><td>{entry.Draft.tier3}</td><td>{entry.Draft.tier4}</td><td>{entry.Draft.tier5}</td><td>{entry.Draft.tier6}</td><td>{entry.Draft.single_number}</td><td>{entry.total_score}</td></tr>"
            user_email = f"<tr><td>{rank}</td><td><a href='{user_profile_url}' style=\"color: blue; max-width: 200px; text-decoration: underline;\">{entry.username}</a></td><td>{entry.Draft.single_number}</td><td>{entry.total_score}</td></tr>"
            leaderboard_entries.append(user_entry)
            leaderboard_email.append(user_email)
            rank += 1

    return leaderboard_entries, leaderboard_email



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

def send_leaderboard_email():
    # Prepare the email body with the leaderboard entries
    app.app_context().push()
    x, leaderboard_entries = get_leaderboard()
    masters = Masters.query.all()
    for entry in masters:
        # Replace '0' with 'E' for r1, r2, r3, r4 for active player's scores
        entry.r1 = 'E' if entry.r1 == '0' else entry.r1
        entry.r2 = 'E' if entry.r2 == '0' else entry.r2
        entry.r3 = 'E' if entry.r3 == '0' else entry.r3
        entry.r4 = 'E' if entry.r4 == '0' else entry.r4
    email_body = render_template('email/leaderboard_email.html', leaderboard=leaderboard_entries, masters=masters)

    all_users = User.query.with_entities(User.email).all()
    recipients = [user.email for user in all_users]

    subject = '[Chi Chi] Leaderboard Report'
    sender = app.config['ADMINS'][0]

    Thread(target=send_email, args=(subject, sender, recipients, "", email_body)).start()