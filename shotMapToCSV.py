from shotMap import *
from statsPuller import * 
from gameToCSV import write_headers, game_exists
import csv
import os


def get_unique_game_links(country):
    country = country.capitalize()
    # List of potential filename patterns
    filename_patterns = [f"{country}.csv",f"{country}_ALL.csv", f"{country}_1ST.csv", f"{country}_2ND.csv"]
    game_links = set()
    # Try each filename until a valid one is found
    for filename in filename_patterns:
        if os.path.exists(filename):  # Check if the file exists
            try:
                with open(filename, newline='', encoding='iso-8859-1') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        game_links.add(row['Game Link'])  # Add the game link to the set
            except Exception as e:
                print(f"An error occurred while reading {filename}: {e}")
                continue  # If an error occurs, try the next file
            break  # If file was successfully processed, stop trying further files
    else:
        # If no files were found or successfully read
        print(f"No valid CSV files found for {country}. Checked files: {filename_patterns}")
        return []

    return list(game_links)  # Return whatever was collected



def shotMapToCSV(gameLink, country):
    fileName = f"{country.capitalize()}_shotmap.csv"
    if game_exists(fileName,gameLink):
        print(f"Game {gameLink} already exists in the CSV. Skipping.")
        return
    match = SoccerMatch(gameLink)
    match.fetch_match_data()
    
    if match.shotMap_json == None:
        print(f"Shotmap not available for {gameLink}, skipping ")
        return
    
    player_stats = extract_dynamic_player_stats(match)

    headers = ["Player", "Game Link", "Country", "shotType", "goalType", "situation",
               "X", "Y", "Z", "bodyPart", "goalMouthLocation",
               "Goal Mouth X", "Goal mouth Y", "Goal Mouth Z","XG","XGOT", "time", "addedTime",
               "timeSeconds", "Start X", "Start Y",  "End X", "End Y", "Goal X", "Goal Y",
               "reversedPeriodTime", "reversedPeriodTimeSeconds", "incidentType"]

    firstEntry = write_headers(fileName, headers)

    with open(fileName, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not firstEntry:
            writer.writerow([])  # Ensures separation between different games
        # Process each player's stats and write a row for each.
        for player_id, data in player_stats.items():
            row = [
                data.get('player_name', 'No information'),
                gameLink,
                data.get('Country', 'No information'),
                data.get('shotType', 'No information'),
                data.get('goalType', 'No information'),
                data.get('situation', 'No information'),
                data.get('playerCoordinates_x', 'No information'),
                data.get('playerCoordinates_y', 'No information'),
                data.get('playerCoordinates_z', 'No information'),
                data.get('bodyPart', 'No information'),
                data.get('goalMouthLocation', 'No information'),
                data.get('goalMouthCoordinates_x', 'No information'),
                data.get('goalMouthCoordinates_y', 'No information'),
                data.get('goalMouthCoordinates_z', 'No information'),
                data.get('XG', 'No information'),  # Assuming 'XG' is expected to be in the stats.
                data.get('XGOT', 'No information'),  # Assuming 'XGOT' is expected to be in the stats.
                data.get('time', 'No information'),
                data.get('addedTime', 'No information'),
                data.get('timeSeconds', 'No information'),
                data.get('draw_start', {}).get('x', 'No information'),
                data.get('draw_start', {}).get('y', 'No information'),
                data.get('draw_end', {}).get('x', 'No information'),
                data.get('draw_end', {}).get('y', 'No information'),
                data.get('draw_goal', {}).get('x', 'No information'),
                data.get('draw_goal', {}).get('y', 'No information'),
                data.get('reversedPeriodTime', 'No information'),
                data.get('reversedPeriodTimeSeconds', 'No information'),
                data.get('incidentType', 'No information')
            ]
            writer.writerow(row)  # Write the player's shot data as a row in the CSV file.
        
