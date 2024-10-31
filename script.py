from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import random
from flask_caching import Cache
from flask_apscheduler import APScheduler
import os
import threading

# Flask app initialization
app = Flask(__name__)
CORS(app)

# Cache configuration
app.config['CACHE_TYPE'] = 'RedisCache'
app.config['CACHE_REDIS_URL'] = os.getenv('CACHE_REDIS_URL', 'redis://redis:6379/0')
cache = Cache(app)

# Scheduler configuration
class Config:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Config)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# Background scraping tasks without Celery, using threading
def scrape_coursera_courses():
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
            a_tag = course.find('a', class_=lambda value: value and 'cds-CommonCard-titleLink' in value)

            if title_element and provider_element:
                title = title_element.text.strip()
                provider = provider_element.text.strip()
                rating = rating_element.text.strip() if rating_element else 'N/A'
                detail = detail_element.text.strip() if detail_element else 'N/A'
                link_href = 'https://www.coursera.org' + a_tag['href'] if a_tag and 'href' in a_tag.attrs else None

                course_data = {
                    "id": idx + 1,
                    "title": title,
                    "provider": "coursera / " + provider,
                    "detail": detail,
                    "rating": rating,
                    "category": "Online Course",
                    "link": link_href
                }
                courses_list.append(course_data)
    return courses_list

def scrape_harvard_courses():
    courses_list = []
    URL2 = 'https://pll.harvard.edu/catalog/free'
    response2 = requests.get(URL2)

    if response2.status_code == 200:
        soup2 = BeautifulSoup(response2.text, 'html.parser')
        harvards = soup2.find_all('div', class_='group-details')

        for idx, harvard in enumerate(harvards, start=len(courses_list) + 1):
            title_element = harvard.find('div', class_='field field---extra-field-pll-extra-field-subject field--name-extra-field-pll-extra-field-subject field--type- field--label-inline clearfix')
            provider_element = harvard.find('h3', class_='field__item')
            course_href = harvard.find('h3', class_='field__item').find('a')['href']
            link_href = 'https://pll.harvard.edu' + course_href

            if title_element and provider_element:
                title = title_element.text.strip()
                provider = provider_element.text.strip()

                course_data = {
                    "id": idx + 1,
                    "title": provider,
                    "provider": "Harvard",
                    "detail": 'N/A',
                    "rating": 'N/A',
                    "category": title,
                    "link": link_href
                }
                courses_list.append(course_data)
    return courses_list

# API endpoint to return all courses with caching
@app.route('/api/courses', methods=['GET'])
@cache.cached(timeout=86400)  # Cache the result for 24 hours
def get_courses():
    coursera_courses = scrape_coursera_courses()
    harvard_courses = scrape_harvard_courses()

    # Assign unique IDs and shuffle the courses
    harvard_start_id = len(coursera_courses) + 1
    for idx, course in enumerate(harvard_courses):
        course["id"] = harvard_start_id + idx

    # Combine all courses into one list and shuffle
    all_courses = coursera_courses + harvard_courses
    random.shuffle(all_courses)

    return jsonify(all_courses)

# Background task runner
def run_background_scraping():
    def background_scrape():
        scrape_coursera_courses()
        scrape_harvard_courses()
    thread = threading.Thread(target=background_scrape)
    thread.start()

# Schedule the task to run periodically (e.g., every day at 02:00 AM)
@scheduler.task('interval', id='scheduled_scraping', hours=24)
def scheduled_task():
    run_background_scraping()

if __name__ == '__main__':
    app.run(debug=True)
