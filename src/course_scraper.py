import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
import logging
import requests

import uuid


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

        for course in courses:
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

        for course in courses: 
            
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

    def get_udacity_courses(self):
        course_list = []
        soup = self._make_request('https://www.classcentral.com/provider/udacity?free=true')

        if not soup:
            return course_list

        courses = soup.find_all('li', class_='course-list-course')

        if not courses:
            return course_list

        for course in courses:
            try:
                title_element = course.find('div', class_='row').find('h2')
                details_element = course.find('div').find('p')
                link = course.find('div', class_='row').find('a')['href']
                rating_element = course.find('div').find('div', class_='row').find('div').find('li', class_='icon-star icon-small')
            
                if not (title_element):
                    continue

                course_data = Course(
                    id=str(uuid.uuid4()),
                    title=title_element.text.strip(),
                    provider="Udacity",
                    detail=details_element.text.strip() if details_element else 'N/A',
                    rating=rating_element.text.strip() if rating_element else 'N/A',
                    category=link,
                    link=link
                )

                course_list.append(vars(course_data))

            except Exception as e:
                logger.error(f"Error parsing Udacity course: {str(e)}")
                continue

        return course_list