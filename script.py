from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import random
import requests

app = Flask(__name__)
CORS(app)

# Function to scrape Coursera courses
def get_coursera_courses():
    courses_list = []
    URL = 'https://www.coursera.org/courses?query=free'
    response = requests.get(URL)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        courses = soup.find_all('div', class_='css-16m4c33')

        for idx, course in enumerate(courses):
            title_element = course.find('h3', class_='cds-CommonCard-title')
            provider_element = course.find('p', class_='cds-ProductCard-partnerNames')
            detail_element = course.find('div', class_='cds-ProductCard-body')
            rating_element = course.find('p', class_='css-2xargn')
            # Find the relevant <a> tag
            a_tag = course.find('a', class_=lambda value: value and 'cds-CommonCard-titleLink' in value)

            if title_element and provider_element:
                title = title_element.text.strip()
                provider = provider_element.text.strip()
                rating = rating_element.text.strip() if rating_element else 'N/A'
                detail = detail_element.text.strip() if detail_element else 'N/A'

                # Extract the link from the <a> tag
                # Extract the href attribute
                link_href = 'https://www.coursera.org' + a_tag['href'] if a_tag and 'href' in a_tag.attrs else None

                course_data = {
                    "id": idx + 1,  # Incremental ID
                    "title": title,
                    "provider": "coursera / " + provider,
                    "detail": detail,
                    "rating": rating,
                    "category": "Online Course", # Default category
                    "link": link_href
                }
                courses_list.append(course_data)

    return courses_list

# Function to scrape Harvard courses
def get_harvard_courses():
    courses_list = []
    URL2 = 'https://pll.harvard.edu/catalog/free'
    response2 = requests.get(URL2)

    if response2.status_code == 200:
        soup2 = BeautifulSoup(response2.text, 'html.parser')
        harvards = soup2.find_all('div', class_='group-details')

        for idx, harvard in enumerate(harvards, start=len(courses_list) + 1):  # Ensure unique ID continues
            title_element = harvard.find('div', class_='field field---extra-field-pll-extra-field-subject field--name-extra-field-pll-extra-field-subject field--type- field--label-inline clearfix')
            provider_element = harvard.find('h3', class_='field__item')

            course_href = harvard.find('h3', class_='field__item').find('a')['href']

            link_href = 'https://pll.harvard.edu' + course_href

            if title_element and provider_element:
                title = title_element.text.strip()
                provider = provider_element.text.strip()

                course_data = {
                    "id": idx + 1,  # Incremental ID
                    "title": provider,
                    "provider": "Harvard",
                    "detail": 'N/A',
                    "rating": 'N/A',
                    "category": title,
                    "link": link_href
                }
                courses_list.append(course_data)


    return courses_list

    courses_list = []
    URL3 = 'https://online.stanford.edu/explore?filter%5B0%5D=free_or_paid%3Afree&keywords=&items_per_page=12'
    
    # Add headers to simulate a browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    
    response3 = requests.get(URL3, headers=headers)

    if response3.status_code == 200:
        soup3 = BeautifulSoup(response3.text, 'html.parser')
        stanfords = soup3.find_all('a', class_='node node--type-course')

        for idx, stanford in enumerate(stanfords, start=len(courses_list) + 1):  # Ensure unique ID continues
            title_element = stanford.find('div', class_='field title')
            provider_element = stanford.find('div', class_='school field field-school')
            detail_element = stanford.find('div', class_='field field-sections')

            link_href = 'https://online.stanford.edu' + stanford['href']

            if title_element and provider_element:
                title = title_element.text.strip()
                provider = provider_element.text.strip()
                detail = detail_element.text.strip() if detail_element else 'N/A'

                course_data = {
                    "id": idx + 1,  # Incremental ID
                    "title": title,
                    "provider": provider,
                    "detail": detail,
                    "rating": 'N/A',
                    "category": "Online courses",
                    "link": link_href
                }
                courses_list.append(course_data)

    return courses_list

# API endpoint to return all courses
@app.route('/api/courses', methods=['GET'])
def get_courses():
    # Fetch courses from different platforms
    coursera_courses = get_coursera_courses()
    harvard_courses = get_harvard_courses()

    # Step 1: Assign unique IDs to Harvard courses after Coursera courses
    harvard_start_id = len(coursera_courses) + 1
    for idx, course in enumerate(harvard_courses):
        course["id"] = harvard_start_id + idx  # Assign new unique ID for Harvard courses

    # Combine all courses into one list
    all_courses = coursera_courses + harvard_courses

    # Optionally shuffle the course list to randomize the order
    random.shuffle(all_courses)

    return jsonify(all_courses)


if __name__ == '__main__':
    app.run(debug=True)
