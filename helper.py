import requests
# from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from flask_mail import Message
import re

from sqlalchemy import or_, and_, func

from app import mail
from flask import url_for
from app import db, app
from app.models import User, Masters, updated, Draft
from sqlalchemy.exc import IntegrityError
from flask import render_template
from threading import Thread
from collections import defaultdict

'''
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
'''


def generate_player_key(name):
    name_without_special_chars = re.sub(r'[^a-zA-Z]+', '', name)
    return name_without_special_chars.upper()


def masters_api():
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"

    querystring = {"orgId": "1", "tournId": "016", "year": "2024"}

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
            'playerId': player.get('firstName') + player.get('lastName'),
            'R1': cleanse_score(next((round_data['scoreToPar'] for round_data in player['rounds'] if
                                      round_data['roundId']['$numberInt'] == '1'), None)),
            'R2': cleanse_score(next((round_data['scoreToPar'] for round_data in player['rounds'] if
                                      round_data['roundId']['$numberInt'] == '2'), None)),
            'R3': cleanse_score(next((round_data['scoreToPar'] for round_data in player['rounds'] if
                                      round_data['roundId']['$numberInt'] == '3'), None)),
            'R4': cleanse_score(next((round_data['scoreToPar'] for round_data in player['rounds'] if
                                      round_data['roundId']['$numberInt'] == '4'), None)),
            'To Par': cleanse_score(player.get('total'))
        }
        player_data.append(player_info)

    # Create DataFrame from extracted data
    player_df = pd.DataFrame(player_data)
    player_df['playerId'] = player_df['playerId'].apply(generate_player_key)

    return player_df


def update_data():
    # scraped_data = scrape_data()  # Scrape data from the website
    scraped_data = masters_api()  # fetch data from api
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
    # player_id = int(player_id)

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
    # First, query the necessary data from the database
    from sqlalchemy.orm import aliased
    t1_masters = aliased(Masters, name='t1_masters')
    t2_masters = aliased(Masters, name='t2_masters')
    t3_masters = aliased(Masters, name='t3_masters')
    t4_masters = aliased(Masters, name='t4_masters')
    t5_masters = aliased(Masters, name='t5_masters')
    t6_masters = aliased(Masters, name='t6_masters')

    query_scores = db.session.query(
        User.username,
        Draft.single_number,
        Draft.tier1,
        t1_masters.to_par.label('t1_to_par'),
        Draft.tier2,
        t2_masters.to_par.label('t2_to_par'),
        Draft.tier3,
        t3_masters.to_par.label('t3_to_par'),
        Draft.tier4,
        t4_masters.to_par.label('t4_to_par'),
        Draft.tier5,
        t5_masters.to_par.label('t5_to_par'),
        Draft.tier6,
        t6_masters.to_par.label('t6_to_par'),
    ).join(Draft).join(t1_masters, Draft.t1_id == t1_masters.playerId) \
        .join(t2_masters, Draft.t2_id == t2_masters.playerId) \
        .join(t3_masters, Draft.t3_id == t3_masters.playerId) \
        .join(t4_masters, Draft.t4_id == t4_masters.playerId) \
        .join(t5_masters, Draft.t5_id == t5_masters.playerId) \
        .join(t6_masters, Draft.t6_id == t6_masters.playerId)

    df_scores = pd.DataFrame(
        query_scores,
        columns=["username", "single_number",
                 "tier1", "t1_to_par",
                 "tier2", "t2_to_par",
                 "tier3", "t3_to_par",
                 "tier4", "t4_to_par",
                 "tier5", "t5_to_par",
                 "tier6", "t6_to_par"],
    )

    # Assuming df_scores is your original DataFrame

    # Create a new DataFrame to store the result
    result_df = pd.DataFrame(columns=["Username", "single_number",
                                      "lowest_player", "second_lowest_player",
                                      "third_lowest_player", "fourth_lowest_player",
                                      "fifth_lowest_player", "highest_player",
                                      "sum_lowest_to_par"])

    # Iterate through each row in the original DataFrame
    for index, row in df_scores.iterrows():
        # Extracting player names and to_par values
        players = [row[f"tier{i}"] for i in range(1, 7)]
        to_pars = [row[f"t{i}_to_par"] for i in range(1, 7)]

        # Sorting players and to_pars based on to_pars
        sorted_data = sorted(zip(players, to_pars), key=lambda x: x[1])

        # Extracting required information for the result DataFrame
        lowest_player, second_lowest_player, third_lowest_player, fourth_lowest_player, fifth_lowest_player, highest_player = sorted_data
        sum_lowest_to_par = sum(to_par for _, to_par in sorted_data[:4])

        # Adding a new row to the result DataFrame
        result_df = result_df.append({
            "username": row["username"],
            "single_number": row["single_number"],
            "lowest_player": f"{lowest_player[0]} (T{players.index(lowest_player[0]) + 1}) ({lowest_player[1]})",
            "second_lowest_player": f"{second_lowest_player[0]} (T{players.index(second_lowest_player[0]) + 1}) ({second_lowest_player[1]})",
            "third_lowest_player": f"{third_lowest_player[0]} (T{players.index(third_lowest_player[0]) + 1}) ({third_lowest_player[1]})",
            "fourth_lowest_player": f"{fourth_lowest_player[0]} (T{players.index(fourth_lowest_player[0]) + 1}) ({fourth_lowest_player[1]})",
            "fifth_lowest_player": f"{fifth_lowest_player[0]} (T{players.index(fifth_lowest_player[0]) + 1}) ({fifth_lowest_player[1]})",
            "highest_player": f"{highest_player[0]} (T{players.index(highest_player[0]) + 1}) ({highest_player[1]})",
            "sum_lowest_to_par": sum_lowest_to_par
        }, ignore_index=True)

    # Below block determines how close a user's predicted score is to the top-ranked player's "to par"
    scores = defaultdict(list)
    for entry in result_df.itertuples():
        total_score = entry.sum_lowest_to_par  # Use the total_score column calculated above
        predicted_score = entry.single_number
        top_player_to_par = Masters.query.order_by(Masters.pos).first().to_par
        score_difference = abs((top_player_to_par) - (predicted_score))

        score = (total_score, score_difference)
        scores[score].append(entry)

    # Sorting the users based on criteria
    sorted_scores = sorted(scores.keys(), key=lambda x: (
        x[0], x[1]))  # Sort by total_score and closest predicted score to top-ranked player's "to par"
    leaderboard_entries = []
    leaderboard_email = []
    rank = 1
    for score in sorted_scores:
        for entry in scores[score]:
            user_profile_url = url_for('user', username=entry.username)
            user_entry = f"<tr><td>{rank}</td><td><a href='{user_profile_url}' style=\"color: blue; max-width: 200px; text-decoration: underline;\">{entry.username}</a></td><td>{entry.sum_lowest_to_par}</td><td>{entry.lowest_player}</td><td>{entry.second_lowest_player}</td><td>{entry.third_lowest_player}</td><td>{entry.fourth_lowest_player}</td><td>{entry.fifth_lowest_player}</td><td>{entry.highest_player}</td><td>{entry.single_number}</td></tr>"
            user_email = f"<tr><td style='border: 1px solid #1a351d; padding: 10px; text-align: center; font-size: 16px;'>{rank}</td><td style='border: 1px solid #1a351d; padding: 10px; text-align: center; font-size: 16px;'><a href='{user_profile_url}' style='color: blue; max-width: 200px; text-decoration: underline;'>{entry.username}</a></td><td style='border: 1px solid #1a351d; padding: 10px; text-align: center; font-size: 16px;'>{entry.single_number}</td><td style='border: 1px solid #1a351d; padding: 10px; text-align: center; font-size: 16px;'>{entry.sum_lowest_to_par}</td></tr>"
            leaderboard_entries.append(user_entry)
            leaderboard_email.append(user_email)
            rank += 1

    return leaderboard_entries, leaderboard_email




def get_leaderboard_old():
    # Fetching Masters data, and computing total_score for a user
    # total_score = tier1 to_par + tier2 to_par + ... + tier6 to_par
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

    #Below block determines how close a user's predicted score is the the top-ranked player's "to par"
    scores = defaultdict(list)
    for entry in leaderboard_data:
        total_score = entry.total_score
        predicted_score = entry.Draft.single_number
        top_player_to_par = Masters.query.order_by(Masters.pos).first().to_par  # Fetching top-ranked player's "To Par"
        score_difference = abs((top_player_to_par) - (predicted_score))

        score = (total_score, score_difference)
        scores[score].append(entry)

    # Sorting the users based on criteria
    sorted_scores = sorted(scores.keys(), key=lambda x: (
    x[0], x[1]))  # Sort by total_score and closest predicted score to top-ranked player's "To Par"
    leaderboard_entries = []
    leaderboard_email = []
    rank = 1
    for score in sorted_scores:
        for entry in scores[score]:
            user_profile_url = url_for('user', username=entry.username)
            user_entry = f"<tr><td>{rank}</td><td><a href='{user_profile_url}' style=\"color: blue; max-width: 200px; text-decoration: underline;\">{entry.username}</a></td><td>{entry.Draft.tier1}</td><td>{entry.Draft.tier2}</td><td>{entry.Draft.tier3}</td><td>{entry.Draft.tier4}</td><td>{entry.Draft.tier5}</td><td>{entry.Draft.tier6}</td><td>{entry.Draft.single_number}</td><td>{entry.total_score}</td></tr>"
            user_email = f"<tr><td style='border: 1px solid #1a351d; padding: 10px; text-align: center; font-size: 16px;'>{rank}</td><td style='border: 1px solid #1a351d; padding: 10px; text-align: center; font-size: 16px;'><a href='{user_profile_url}' style='color: blue; max-width: 200px; text-decoration: underline;'>{entry.username}</a></td><td style='border: 1px solid #1a351d; padding: 10px; text-align: center; font-size: 16px;'>{entry.Draft.single_number}</td><td style='border: 1px solid #1a351d; padding: 10px; text-align: center; font-size: 16px;'>{entry.total_score}</td></tr>"
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
        entry.r1 = 'E' if entry.r1 == '0' else '-' if entry.r1 == "None" else entry.r1
        entry.r2 = 'E' if entry.r2 == '0' else '-' if entry.r2 == "None" else entry.r2
        entry.r3 = 'E' if entry.r3 == '0' else '-' if entry.r3 == "None" else entry.r3
        entry.r4 = 'E' if entry.r4 == '0' else '-' if entry.r4 == "None" else entry.r4
    email_body = render_template('email/leaderboard_email.html', leaderboard=leaderboard_entries, masters=masters)

    all_users = User.query.with_entities(User.email).all()
    recipients = [user.email for user in all_users]

    subject = '[Chi Chi] Leaderboard Report'
    sender = app.config['ADMINS'][0]

    Thread(target=send_email, args=(subject, sender, recipients, "", email_body)).start()


def send_welcome_email(user, email):
    email_body = render_template('email/welcome_email.html', user=user)

    subject = '[Chi Chi] Confirmation of Registration'
    sender = app.config['ADMINS'][0]

    Thread(target=send_email, args=(subject, sender, [email], "", email_body)).start()
