import requests
from bs4 import BeautifulSoup
import sqlite3

# Create or connect to SQLite database
conn = sqlite3.connect('courses.db')
cursor = conn.cursor()

# Create a table to store courses if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    provider TEXT NOT NULL
)
''')

# URL of the website with free courses
URL = ''

# Send a GET request to fetch the page content
response = requests.get(URL)

# Check if the request was successful
if response.status_code == 200:
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all the course elements (update the tag and class based on the site structure)
    courses = soup.find_all('div', class_='css-16m4c33')

        # Find all image elements
    images = soup.find_all('img')
    
    # Loop through each image and extract the src attribute (image URL)
    for img in images:
        img_url = img.get('src')
        if img_url:
            print(f'Image URL: {img_url}')
            print('---')
    
    # Loop through each course and extract title and provider
    for course in courses:
        # Extract the course title
        title_element = course.find('h3', class_='cds-CommonCard-title')
        provider_element = course.find('p', class_='cds-ProductCard-partnerNames')

        # If title or provider elements are missing, skip this course
        if title_element is not None and provider_element is not None:
            title = title_element.text.strip()
            provider = provider_element.text.strip()

            # Insert course data into the database
            cursor.execute('''
            INSERT INTO courses (title, provider) 
            VALUES (?, ?)
            ''', (title, provider))

            print(f'Course: {title}')
            print(f'Provider: {provider}')
            print('---')

    # Commit the changes to the database
    conn.commit()
else:
    print(f"Failed to retrieve the webpage. Status code: {response.status_code}")

# Close the database connection
conn.close()
