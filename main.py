from linkGrabber import *
from gameToCSV import gameToCSV
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor, as_completed
from shotMapToCSV import *

# gets game stats for a country and stores it in a csv 
def fetch_and_store_game_data(game_link, country, period):
    """Fetch and store game data for a given link, with detailed error handling."""
    try:
        gameToCSV(game_link, country, period)
    except Exception as e:
        # Now includes the game link in the error message for better tracking
        print(f"Error processing {game_link} for {country}: {e}")
        
def fetch_and_store_shotmap_data(game_link, country):
    """Fetch and store game data for a given link, with detailed error handling."""
    try:
        shotMapToCSV(game_link, country)
    except Exception as e:
        # Now includes the game link in the error message for better tracking
        print(f"Error processing shotmap {game_link} for {country}: {e}")


def get_game_links(params):
    country, number = params
    return numberOfGames(country, number)

    
def main():
    countries = []
    valid_integer = False
    while not valid_integer:
        choice =  input("Would you like to 1) get the game stats for a country 2) grab the shotmap statistics ")
        try:
            choice = int(choice)
            if choice == 1 or choice == 2:
                valid_integer = True
        except ValueError:
            print("Please enter a valid integer")
            
    if choice == 1:
        while True:
            country = input("Enter a country to get stats for, or type 'done' to finish: ").strip().lower()
            if country == 'done':
                break
            if country in countries:
                print("You've already entered that country. Please enter another.")
                continue
            countries.append(country)

        countryNumber = []
        for country in countries:
            formatted_country = country.capitalize()
            valid_input = False
            while not valid_input:
                number = input(f"How many {formatted_country} games would you like to scrape? ")
                try:
                    number = int(number)
                    valid_input = True
                    countryNumber.append(number)
                except ValueError:
                    print("Please enter a valid integer")
        
        countryGames = {}
        
        params = list(zip(countries, countryNumber))
        
        # Use multiprocessing to fetch game links
        with Pool(5) as pool:
            results = pool.map(get_game_links, params)

        countryGames = {country: result for (country, _), result in zip(params, results) if result != "Country not found"}   
        
        valid_periods = ["ALL", "1ST", "2ND"]
        while True:
            period = input(f"What period would you like to retrieve data for? (ALL) (1ST) (2ND) ")
            if period in valid_periods:
                break  # Break the loop if input is valid
            else:
                print("Please enter a valid period (ALL, 1ST, 2ND)")
            
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for country, games in countryGames.items():
                for game_link in games:
                    futures.append(executor.submit(fetch_and_store_game_data, game_link, country, period))

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Error processing a game link: {e}")
    if choice == 2:
        while True:
            country = input("Enter a country to get shotmap stats for, or type 'done' to finish. NOTE countryname.csv must be available to get shotMap Data: ").strip().lower()
            if country == 'done':
                break
            if country in countries:
                print("You've already entered that country. Please enter another.")
                continue
            countries.append(country)

        gameLinks = {}
        for c in countries:
            gameLinks[c] = get_unique_game_links(c)
            
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for country, games in gameLinks.items():
                for game_link in games:
                    futures.append(executor.submit(fetch_and_store_shotmap_data, game_link, country))

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Error processing a game link: {e}")

        
        
        
    print("Done! CSV files saved to the same directory as main.py")


if __name__ == "__main__":
    main()


