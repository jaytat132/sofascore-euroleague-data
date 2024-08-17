import csv
import os
from statsPuller import *

# Prevent Excel from converting it to date
def format_for_csv(value):
    if '/' in value and value.count('/') == 1 and all(part.isdigit() for part in value.split('/')):
        return "'" + value  
    return value

# Checks if gamme is already present in the excel sheet
def game_exists(file_path, game_link):
    """Check if the game already exists in the CSV file."""
    if not os.path.exists(file_path):
        return False
    with open(file_path, mode='r', newline='') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header
        for row in reader:
            if game_link in row:  
                return True
    return False

# Writes the heaaders, also checks if csv file exists 
def write_headers(file_path, headers):
    # Check if file exists and has content
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return False  # Headers are not written because the file already has content
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
    return True  # Headers are written

# Converts game data into csv file 
def gameToCSV(gameLink, country, period):
    filename = f"{country.capitalize()}_{period.upper()}.csv"
    if game_exists(filename,gameLink):
        print(f"Game {gameLink} already exists in the CSV. Skipping.")
        return
    
    match = SoccerMatch(gameLink)
    match.fetch_match_data()
    statsJson = statisticsGrabber(match.statistics_urls)
    
    if(statsJson == None):
        print(f"Match data not available for {gameLink}, skipping.")
        return
    
    team1_data, team1_name = extract_period_data(statsJson,period.upper())[0], match.home_team.capitalize()
    team2_data, team2_name = extract_period_data(statsJson,period.upper())[1], match.away_team.capitalize()

    team1_data["Goals"] = match.home_scores
    team2_data["Goals"] = match.away_team_scores
    # Define a comprehensive list of all possible headers
    headers = [
        'Team', 'Game Link', 'Ball possession', 'Expected goals', 'Big chances', 'Total shots', 'Goalkeeper saves',
        'Corner kicks', 'Fouls', 'Passes', 'Tackles', 'Free kicks', 'Yellow cards', 'Red cards', 'Shots on target',
        'Hit woodwork', 'Shots off target', 'Blocked shots', 'Shots inside box', 'Shots outside box', 'Big chances scored',
        'Big chances missed', 'Through balls', 'Touches in penalty area', 'Fouled in final third', 'Offsides',
        'Accurate passes', 'Throw-ins', 'Final third entries', 'Long balls', 'Crosses', 'Duels', 'Dispossessed',
        'Ground duels', 'Aerial duels', 'Dribbles', 'Tackles won', 'Total tackles', 'Interceptions', 'Recoveries',
        'Clearances', 'Goals prevented', "Goalkeeper saves",'Goal kicks','Goals','Date'
    ]

    first_entry = write_headers(filename, headers)  # Ensure headers are written only if file is empty

    # Function to populate row data for a team
    def create_row(team_data, team_name):
        row = [team_name, gameLink]
        for header in headers[2:-1]:  # Skip 'Team' and 'Game Link' which are already handled, and make it -1 for the date
            row.append(format_for_csv(team_data.get(header, "No information")))
        row.append(match.date)
        return row

    team1_row = create_row(team1_data, team1_name)
    team2_row = create_row(team2_data, team2_name)

    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not first_entry:
            writer.writerow([])  # Ensures separation between different games
        writer.writerow(team1_row)
        writer.writerow(team2_row)

