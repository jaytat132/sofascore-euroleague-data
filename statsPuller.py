import requests
import json
import re
import psutil
from datetime import datetime
from selenium import webdriver # selenium 4.20.0
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

from webdriver_manager.chrome import ChromeDriverManager # version 4.0.1

def terminate_process_tree(pid):
    """ Terminates a process and all its descendants. """
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.terminate()
        parent.terminate()
    except psutil.NoSuchProcess:
        pass
    
class SoccerMatch:
    def __init__(self, game_link):
        self.game_link = game_link
        self.home_team = None
        self.away_team = None
        self.home_scores = None
        self.away_team_scores = None
        self.statistics_urls = []
        self.date = None
        self.shotMap_json = None
    
    def fetch_match_data(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-dev-shm-usage") 
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36")
        options.set_capability("goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"}
        )
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        retries = 5
        attempt = 0
        
        while attempt < retries:
            try:
                gameLink = self.game_link + ",tab:statistics"
                driver.get(gameLink) 
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                team_names = [span.text.lower() for span in soup.find_all('bdi', class_="Text elglCn")]
                date = [span.text.lower() for span in soup.find_all('bdi', class_="Text bVXOom")]
                home_goals = [span.text.lower() for span in soup.find_all('span', class_="Text cuVfWD")]
                away_goals = [span.text.lower() for span in soup.find_all('span', class_="Text hzbACF")]
                
                if home_goals and away_goals:
                    self.home_scores = home_goals[0]
                    self.away_team_scores = away_goals[0]
                else:
                    tie_goals = [span.text.lower() for span in soup.find_all('span', class_="Text hzbACF")]
                    if tie_goals:
                        self.home_scores = tie_goals[0]
                        self.away_team_scores = tie_goals[0]
                    
                if date:
                    self.date = date[0]
                else:
                    date = [span.text.lower() for span in soup.find_all('div', class_="Text feHXxp")]
                    match = re.search(r'(\d{1,2} \w+ \d{4}) at (\d{2}:\d{2})', date[0])
                    if match:
                        date_str, time_str = match.groups()
                        # Combine the date and time strings
                        full_date_str = f"{date_str} {time_str}"
                        # Parse the date and time
                        dt = datetime.strptime(full_date_str, "%d %b %Y %H:%M")
                        # Format the datetime object to the desired format
                        formatted_date = dt.strftime("%m/%d/%Y, %H:%M")
                        self.date = formatted_date
                    
                if len(team_names) == 2:
                    self.home_team, self.away_team = team_names
                    
                logs_raw = driver.get_log("performance")
                statiticsPattern = re.compile(r"https://www\.sofascore\.com/api/v1/event/\d+/statistics")
                logs = [json.loads(lr["message"])["message"] for lr in logs_raw]
                for x in logs:
                    if 'shotmap' in x['params'].get('headers', {}).get(':path', ''):
                        x['params'].get('headers', {}).get(':path')
                        url = "https://www.sofascore.com" + x['params'].get('headers', {}).get(':path')
                        if(statisticsGrabberNonArr(url) == None):
                            json_file = None
                        else:
                            json_file = json.loads(driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': x["params"]["requestId"]})['body'])['shotmap']
                            self.shotMap_json = json_file 
                        break
                
                for lr in logs_raw:
                    message = json.loads(lr["message"])["message"]
                    url = message['params'].get('headers', {}).get(':path', '')
                    full_url = "https://www.sofascore.com" + url
                    if statiticsPattern.match(full_url) and full_url not in self.statistics_urls:
                        self.statistics_urls.append(full_url)
                
                break
            except Exception as e:
                attempt += 1
                print(f"Attempt {attempt}: Failed to load page, error: {e}")
                if attempt == retries:
                    print("Max retries reached, moving on...")
            finally:
                terminate_process_tree(driver.service.process.pid)
                driver.quit()
        
# Grabs the Json from an array of urls
def statisticsGrabber(urls):
    # Get request to the url 
    for url in urls:      
        response = requests.get(url)
        # Check if the request was successful
        if response.status_code == 200:
            # Load the JSON data from the response
            data = response.json()
            return data
    return None

# Grabs the json from one url 
def statisticsGrabberNonArr(url):
    # Get request to the url 
    response = requests.get(url)
    # Check if the request was successful
    if response.status_code == 200:
        # Load the JSON data from the response
        data = response.json()
        return data
    return None

# Extracts statistics data from a specified period of time ("ALL", "1ST, "2ND")
def extract_period_data(data, period):
    home_stats = {}
    away_stats = {}
    if "error" in data:
        print(f"Error {data['error']['code']}: {data['error']['message']}")
        return None, None
    for item in data['statistics']:
        if item['period'] == period:
            for group in item['groups']:
                for stat in group['statisticsItems']:
                    home_stats[stat['name']] = stat.get('home', 'N/A')
                    away_stats[stat['name']] = stat.get('away', 'N/A')
            break
    
    return home_stats, away_stats

