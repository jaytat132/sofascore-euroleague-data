import re
from requests_html import HTMLSession
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from statsPuller import terminate_process_tree


# Driver options
options = Options()
options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-extensions")
options.add_argument("--log-level=3")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36")
service = Service(ChromeDriverManager().install())


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
    countryNames = [span.text.lower() for span in soup.find_all('div', class_="Text GvzuH")]
    session.close()
    # Check if the normalized input country is in the normalized list of country names
    if country.lower() in countryNames:
        # Find the href link and return it back
        # if input = türkiye or czechia set it to the href value in the url (these are edge cases)
        if(country.lower() == 'türkiye' or country.lower() == 'czechia'):
            if country.lower == 'türkiye':
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

    # Locate the div with the class 'Box irQsdO'
    div_element = soup.find("div", class_="Box irQsdO")

    # Ensure the div_element was found before proceeding
    if not div_element:
        print("Error: The specified div with class 'Box irQsdO' was not found in the HTML.")
        
    # Find all <a> tags with href within the specified div
    a_elements = div_element.find_all('a', href=True)
    base_url = "https://www.sofascore.com"
    # Extract the href attributes and store them in an array
    href_links = [base_url + a['href'] for a in a_elements if a['href'].startswith('/')]

    # if input = türkiye or czechia set it to the href value in the url (these are edge cases)
    if(country.lower() == 'türkiye' or country.lower() == 'czechia'):
        if country.lower == 'türkiye':
            country = "turkey"
        else:
            country = 'czech-republic'
    # Define the regex pattern to match links
    pattern = re.compile(rf'.*{country.lower()}.*')  # Adjusted regex

    # Filter the href_links based on the pattern
    filtered_links = [link for link in href_links if pattern.search(link)]
    return filtered_links

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
    html_content = driver.execute_script("return document.documentElement.outerHTML")
    gameLinks = grabLinks(html_content,country)
    if number < 9:
        try:            
            gameLinks = grabLinks(html_content,country)
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
            # Gets the newly loaded html 
            new_html_content = driver.execute_script("return document.documentElement.outerHTML")
            # Grabs game links from the new html file
            new_game_links = grabLinks(new_html_content, country)
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
    
    
