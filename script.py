import requests
from bs4 import BeautifulSoup
import csv

# CSV file to store courses
csv_file = 'courses.csv'

# Open CSV file in write mode
with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)

    # Write the header row
    writer.writerow(['Title', 'Provider', 'Detail'])

    # URL of the websites with free courses
    URL = 'https://www.coursera.org/courses?query=free'
    URL2 = 'https://pll.harvard.edu/catalog/free'

    # Send a GET request to fetch the page content for Coursera
    response = requests.get(URL)

    # Check if the request was successful for Coursera
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        courses = soup.find_all('div', class_='css-16m4c33')

        for course in courses:
            title_element = course.find('h3', class_='cds-CommonCard-title')
            provider_element = course.find('p', class_='cds-ProductCard-partnerNames')
            detail_element = course.find('div', class_='cds-ProductCard-body')

            if title_element is not None and provider_element is not None:
                title = title_element.text.strip()
                provider = provider_element.text.strip()

                # Check if detail_element exists before extracting text
                if detail_element is not None:
                    detail = detail_element.text.strip()
                else:
                    detail = 'N/A'  # Assign a default value if detail is not found

                # Write the data to the CSV file
                writer.writerow([title, provider, detail])

                print(f'Course: {title}')
                print(f'Provider: {provider}')
                print(f'Detail: {detail}')
                print('---')
    else:
        print(f"Failed to retrieve Coursera webpage. Status code: {response.status_code}")

    # Send a GET request to fetch the page content for Harvard
    response2 = requests.get(URL2)

    # Check if the request was successful for Harvard
    if response2.status_code == 200:
        soup2 = BeautifulSoup(response2.text, 'html.parser')

        # DEBUG: Log the HTML response to inspect the structure
        # print("Harvard HTML response:")
        # print(soup2.prettify())

        oxfords = soup2.find_all('div', class_='group-details')

        # if not oxfords:
        #     print("No 'group-details' elements found. Check the HTML structure.")
        
        for oxford in oxfords:
            title_element = oxford.find('div', class_='field field---extra-field-pll-extra-field-subject field--name-extra-field-pll-extra-field-subject field--type- field--label-inline clearfix')
            provider_element = oxford.find('h3', class_='field__item')

            if title_element is not None and provider_element is not None:
                title = title_element.text.strip()
                provider = provider_element.text.strip()

                # Write the data to the CSV file
                writer.writerow([title, provider])

                print(f'Course: {title}')
                print(f'Provider: {provider}')
                print('---')
    else:
        print(f"Failed to retrieve Harvard webpage. Status code: {response2.status_code}")

print(f"Data has been successfully written to {csv_file}")
