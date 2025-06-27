import re
import os
from requests_html import HTMLSession
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from statsPuller import terminate_process_tree


# Driver options
options = Options()
options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
options.add_argument("--disable-gpu")
options.add_argument('--headless=new')
options.add_argument("--no-sandbox")
options.add_argument("--disable-extensions")
options.add_argument("--log-level=3")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36")
chrome_install = ChromeDriverManager().install()
folder = os.path.dirname(chrome_install)
chromedriver_path = os.path.join(folder, "chromedriver.exe")
service = ChromeService(chromedriver_path)


# We are focused on UEFA nations league for now 
# This function gets a chosen countries url link 
def countryChooser(country):
    session = HTMLSession()
    r = session.get("https://www.sofascore.com/tournament/football/europe/uefa-nations-league/10783#id:58337")
    
    # Render the page to execute JavaScript
    r.html.render(sleep = 1)
    
    # Use BeautifulSoup to parse the rendered HTML
    soup = BeautifulSoup(r.html.raw_html, "html.parser")
    
    # Extract and normalize the country names
    countryNames = [span.text.lower() for span in soup.find_all('div', class_="Text fsoviT")]
    session.close()
    # Check if the normalized input country is in the normalized list of country names
    if country.lower() in countryNames:
        # Find the href link and return it back
        # if input = türkiye or czechia set it to the href value in the url (these are edge cases)
        if(country.lower() == 'türkiye' or country.lower() == 'czechia'):
            if country.lower() == 'türkiye':
                country = "turkey"
            else:
                country = 'czech-republic'
        pattern = f'/team/football/{country.lower()}/\\d+'
        link = re.findall(pattern, str(soup))
        return "https://www.sofascore.com/" + link[0]
    return "Country not found"    
    
# This function gets all the game links from a countries page 
def grabLinks(html, country):
    soup = BeautifulSoup(html, 'html.parser')
    
    # Pulls all the hrefs from the box
    hrefs = [a['href'] for a in soup.find_all('a', href=True)]
    
    # Regex pattern to match the hrefs we want, that is the matches 
    pattern = re.compile(r'^/football/match/([a-zA-Z]+)-(turkiye|[a-zA-Z]+)/.*$')
    
    # Filter the href list to only include matches
    filtered_hrefs = [href for href in hrefs if pattern.match(href)]

    base_url = "https://www.sofascore.com"
    
    # Prepend the base url to the hrefs
    href_links = [base_url + href for href in filtered_hrefs]
    
    return href_links

# This function returns a list of the games a country has played, the size of the list is based on user input 
def numberOfGames(country,number):
    # create the driver to access the games later
    driver = webdriver.Chrome(service=service, options=options)
    url = countryChooser(country)

    if url == "Country not found":
        try:
            pass
        finally:
            if driver:
                try:
                    terminate_process_tree(driver.service.process.pid)
                except Exception as e:
                    print(f"An error occurred while trying to close the driver: {e}")
                finally:
                    driver.quit()
        return "Country not found"
    driver.get(url)
    box_div = WebDriverWait(driver, 5).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "div.Box.irQsdO"))
)
    innerHtml = box_div.get_attribute("innerHTML")
    gameLinks = grabLinks(innerHtml,country)
    if number < 9:
        try:            
            gameLinks = gameLinks
        finally:
            if driver:
                try:
                    terminate_process_tree(driver.service.process.pid)
                except Exception as e:
                    print(f"An error occurred while trying to close the driver: {e}")
                finally:
                    driver.quit()
            
        return gameLinks[:int(number)]
    # First page has two games that haven't played yet, so add two to num to get correct amount of matches
    number += 2
    try:
        for i in range(int(number)//10):
            # Wait for the button to be clickable and then click it
            
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".Button.iCnTrv"))
            ).click()
            # Gets the newly loaded box 
            
            box_div = WebDriverWait(driver, 5).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "div.Box.irQsdO"))
)
            # Grabs game links from the new box
            new_game_links = grabLinks(box_div.get_attribute("innerHTML"), country)
            # Adds it to the current array
            gameLinks.extend(new_game_links)


    finally:
        # Clean up after 
        if driver:
            try:
                terminate_process_tree(driver.service.process.pid)
            except Exception as e:
                print(f"An error occurred while trying to close the driver: {e}")
            finally:
                driver.quit()
    return gameLinks[:int(number)]
    


