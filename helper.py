import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from flask_login import current_user
from app import db, app
from app.models import Masters, updated, Draft
from sqlalchemy.exc import IntegrityError

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
    #if table:
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
    #print("Headers:", headers)
    #if data:
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
    #print(d)

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
