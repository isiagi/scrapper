from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
import random
import logging
import requests
from concurrent.futures import ThreadPoolExecutor
import uuid
import time
import os
from dotenv import load_dotenv

load_dotenv()


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Course:
    id: str
    title: str
    provider: str
    detail: str
    rating: str
    category: str
    link: str



class CourseScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

    def _make_request(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
        
    def get_coursera_courses(self):
        courses_list = []
        soup = self._make_request('https://www.coursera.org/courses?query=free')

        if not soup:
            return courses_list

        courses = soup.find_all('div', class_='css-16m4c33')

        for idx, course in enumerate(courses):
            try:
                title_element = course.find('h3', class_='cds-CommonCard-title')
                provider_element = course.find('p', class_='cds-ProductCard-partnerNames')
                detail_element = course.find('div', class_='cds-ProductCard-body')
                rating_element = course.find('p', class_='css-2xargn')
                # Find the relevant <a> tag
                a_tag = course.find('a', class_=lambda value: value and 'cds-CommonCard-titleLink' in value)

                if not (title_element and provider_element and a_tag):
                    continue

                link_href = link_href = f"https://www.coursera.org{a_tag['href']}" if a_tag and 'href' in a_tag.attrs else None

                course_data = Course(
                    id=str(uuid.uuid4()),
                    title=title_element.text.strip(),
                    provider=f"coursera / {provider_element.text.strip()}",
                    detail=detail_element.text.strip() if detail_element else 'N/A',
                    rating=rating_element.text.strip() if rating_element else 'N/A',
                    category=provider_element.text.strip(),
                    link=link_href
                )

                courses_list.append(vars(course_data))

            except Exception as e:
                logger.error(f"Error parsing Coursera course: {str(e)}")
                continue

        return courses_list
    

    def get_harvard_courses(self):
        course_list = []
        soup = self._make_request('https://pll.harvard.edu/catalog/free')

        if not soup:
            return course_list

        courses = soup.find_all('div', class_='group-details')

        for idx, course in enumerate(courses, start=len(course_list) + 1):  # Ensure unique ID continues
            try:
                title_element = course.find('div', class_='field field---extra-field-pll-extra-field-subject field--name-extra-field-pll-extra-field-subject field--type- field--label-inline clearfix')
                provider_element = course.find('h3', class_='field__item')
                course_href = provider_element.find('a')['href']

                if not (title_element and provider_element):
                    continue

                course_data = Course(
                    id=str(uuid.uuid4()),
                    title=provider_element.text.strip(),
                    provider="Harvard",
                    detail='N/A',
                    rating='N/A',
                    category=title_element.text.strip(),
                    link=f"https://pll.harvard.edu{course_href}"
                )

                course_list.append(vars(course_data))

            except Exception as e:
                logger.error(f"Error parsing Harvard course: {str(e)}")
                continue

        return course_list


def create_app():
    app = Flask(__name__)
    CORS(app)
    scraper = CourseScraper()


    @app.route("/api/courses", methods=["GET"])
    def get_courses():
        try:
            # Sequential execution with detailed timing
            sequential_start = time.time()
            
            coursera_start = time.time()
            coursera_courses_seq = scraper.get_coursera_courses()
            coursera_time = time.time() - coursera_start
            
            harvard_start = time.time()
            harvard_courses_seq = scraper.get_harvard_courses()
            harvard_time = time.time() - harvard_start
            
            sequential_time = time.time() - sequential_start
            
            logger.info(f"Sequential timing details:")
            logger.info(f"  Coursera fetch: {coursera_time:.2f}s")
            logger.info(f"  Harvard fetch: {harvard_time:.2f}s")
            logger.info(f"  Total sequential: {sequential_time:.2f}s")

            # Parallel execution with detailed timing
            parallel_start = time.time()

            # Parallel execution
            with ThreadPoolExecutor(max_workers=2) as executor:
                coursera_future = executor.submit(scraper.get_coursera_courses)
                coursera_courses = coursera_future.result()

                harvard_future = executor.submit(scraper.get_harvard_courses)
                harvard_courses = harvard_future.result()

                
                # Time each future separately
                c_start = time.time()
                coursera_courses = coursera_future.result()
                c_time = time.time() - c_start
                
                h_start = time.time()
                harvard_courses = harvard_future.result()
                h_time = time.time() - h_start

                parallel_time = time.time() - parallel_start
            
                logger.info(f"Parallel timing details:")
                logger.info(f"  Coursera result wait: {c_time:.2f}s")
                logger.info(f"  Harvard result wait: {h_time:.2f}s")
                logger.info(f"  Total parallel: {parallel_time:.2f}s")

                speedup = sequential_time / parallel_time if parallel_time > 0 else 0

                print({
                        "timing": {
                "sequential": {
                    "coursera_time": f"{coursera_time:.2f}s",
                    "harvard_time": f"{harvard_time:.2f}s",
                    "total_time": f"{sequential_time:.2f}s"
                },
                "parallel": {
                    "coursera_wait": f"{c_time:.2f}s",
                    "harvard_wait": f"{h_time:.2f}s",
                    "total_time": f"{parallel_time:.2f}s"
                },
                "speedup_factor": f"{speedup:.2f}x"
            }
                    })

                all_courses = coursera_courses + harvard_courses
                random.shuffle(all_courses)
                return jsonify(all_courses)
        except Exception as e:
            logger.error(f"Error in get_courses endpoint: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "An error occurred while fetching courses",
                "error": str(e)
            }), 500
        

    return app


if __name__ == "__main__":
    app = create_app()
    debug_mode = os.environ.get('FLASK_ENV') == 'development'

    app.run(host='0.0.0.0', debug=debug_mode)
