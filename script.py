from selenium import webdriver
from bs4 import BeautifulSoup

# Set up Selenium with your browser's WebDriver
driver = webdriver.Chrome()

# Load the webpage
driver.get("")

# Extract the page source after JavaScript has loaded
page_source = driver.page_source

# Use BeautifulSoup to parse the dynamically loaded content
soup = BeautifulSoup(page_source, 'html.parser')

# Now you can proceed with your scraping logic
course_container = soup.find('div', class_='course-card_container__urXwO')
if course_container:
    title_tag = course_container.find('h3', class_='ud-heading-md')
    title = title_tag.get_text(strip=True) if title_tag else 'No title found'
    print(f'Title: {title}')

# Close the driver after use
driver.quit()
