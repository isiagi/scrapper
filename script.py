import requests
from bs4 import BeautifulSoup
import csv

# CSV file to store courses
csv_file = 'courses.csv'

# Open CSV file in write mode
with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)

    # Write the header row
    writer.writerow(['Title', 'Provider', 'Rating', 'Skills'])

    # URL of the websites with free courses
    URL = 'https://www.coursera.org/courses?query=free'
  

    # Send a GET request to fetch the page content for Coursera
    response = requests.get(URL)

    # Check if the request was successful for Coursera
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        courses = soup.find_all('div', class_='css-16m4c33')

        for course in courses:
            title_element = course.find('h3', class_='cds-CommonCard-title')
            provider_element = course.find('p', class_='cds-ProductCard-partnerNames')
            detail_element = course.find('div', class_='cds-CommonCard-bodyContent')
            rating_element = course.find('p', class_='css-2xargn')


            if title_element is not None and provider_element is not None:
                title = title_element.text.strip()
                provider = provider_element.text.strip()
                rating = rating_element.text.strip()
               
                                # Check if detail_element exists before extracting text
                if detail_element is not None:
                    detail = detail_element.text.strip()
                else:
                    detail = 'N/A'  # Assign a default value if detail is not found

                # Write the data to the CSV file
                writer.writerow([title, provider, rating, detail])

                print(f'Course: {title}')
                print(f'Provider: {provider}')
                print(f'Rating: {rating}')
                print(f'Skills: {detail}')
                print('---')
    else:
        print(f"Failed to retrieve Coursera webpage. Status code: {response.status_code}")

   

print(f"Data has been successfully written to {csv_file}")


