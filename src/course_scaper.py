import requests
from bs4 import BeautifulSoup
import random
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor



class Scraper:
    def __init__(self):
        self.session = requests
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)  # Basic configuration for logging
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/83.0",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0",
        ]

    def _get_random_headers(self) -> dict:
        """Generate random headers for requests"""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }

    def _make_request(self, url: str, timeout: int = 10):
        """Make HTTP request with error handling and random headers"""
        try:
            headers = self._get_random_headers()
            response = self.session.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            self.logger.error(f"Error fetching URL {url}: {e}")
            return None

    def _fetch_coursera_page(self, page: int):
        """Fetch a single Coursera page with enhanced logging."""
        base_url = 'https://www.coursera.org/courses?query=free'
        url = f"{base_url}&page={page}&index=prod_all_launched_products_term_optimization"
        # self.logger.info(f"Fetching Coursera page: {url}")
        # print(f"Fetching Coursera page: {url}")
        
        response = self._make_request(url)
        if response:
            # self.logger.info(f"Successfully fetched page {page}")
            # print(f"Successfully fetched page {page}")
            return response.text
        else:
            self.logger.error(f"Failed to fetch Coursera page {page}")
            # print(f"Failed to fetch Coursera page {page}")
        return None

    def scrape_coursera(self):
        """Scrape multiple pages of Coursera courses concurrently"""
        courses_list = []
        page_numbers = range(1, 9)  # Fetch first 3 pages

        try:
            with ThreadPoolExecutor(max_workers=8) as executor:
                # Fetch all pages concurrently
                page_contents = list(executor.map(self._fetch_coursera_page, page_numbers))

            for page_content in page_contents:
                if page_content is None:
                    continue

                soup = BeautifulSoup(page_content, "html.parser")
                courses = soup.find_all('div', class_='css-16m4c33')

                for course in courses:
                    try:
                        title_element = course.find('h3', class_='cds-CommonCard-title')
                        provider_element = course.find('p', class_='cds-ProductCard-partnerNames')
                        detail_element = course.find('div', class_='cds-ProductCard-body')
                        rating_element = course.find('p', class_='css-2xargn')
                        a_tag = course.find('a', class_=lambda value: value and 'cds-CommonCard-titleLink' in value)
                        image_element = course.find('div', class_='cds-CommonCard-previewImage').find('img')
            
                        if image_element and 'src' in image_element.attrs:
                            img_url = image_element['src']
                            # print(f"Found image URL: {img_url}")
                            base_url = "https://d3njjcbhbojbot.cloudfront.net/api/utilities/v1/imageproxy/"
                            image_url = img_url.replace(base_url, "")
                        else:
                            print("No image found for this course.")

                        if not (title_element and provider_element and a_tag):
                            continue

                        course_data = {
                            "id": str(uuid.uuid4()),  # Generate a unique ID
                            "title": title_element.text.strip(),
                            "provider": f"coursera / {provider_element.text.strip()}",
                            "detail": detail_element.text.strip() if detail_element else 'N/A',
                            "rating": rating_element.text.strip() if rating_element else 'N/A',
                            "category": provider_element.text.strip(),
                            "link": f"https://www.coursera.org{a_tag['href']}",
                            "image": image_url
                        }
                        # print('course data', course_data)
                        courses_list.append(course_data)

                    except Exception as e:
                        self.logger.error(f"Error parsing Coursera course: {str(e)}")
                        continue

            # self.logger.info(f"Fetched {len(courses_list)} Coursera courses from {len(page_numbers)} pages")
            return courses_list

        except Exception as e:
            self.logger.error(f"Error in concurrent Coursera scraping: {str(e)}")
            return []

    def scrape_harvard_courses(self):
        """Scrape courses from Harvard's online course catalog"""
        courses_list = []
        URL = 'https://pll.harvard.edu/catalog/free'
        response = self._make_request(URL)

        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            harvards = soup.find_all('div', class_='group-details')
            harvard_images = soup.find_all('div', class_='node__content')

            for harvard, harvard_image in zip(harvards, harvard_images):
                try:
                    title_element = harvard.find('div', class_='field field---extra-field-pll-extra-field-subject field--name-extra-field-pll-extra-field-subject field--type- field--label-inline clearfix')
                    provider_element = harvard.find('h3', class_='field__item')
                    course_href = harvard.find('h3', class_='field__item').find('a')['href']
                    link_href = 'https://pll.harvard.edu' + course_href
                    image_element = harvard_image.find('div', class_='field__item').find('a').find('img')

                    if image_element and 'src' in image_element.attrs:
                        img_url = image_element['src']
                        # print(f"Found image URL: {img_url}")
                        # add https://pll.harvard.edu/ to the image URL
                        img_url = 'https://pll.harvard.edu' + img_url
                        
                    else:
                        print("No image found for this course.")

                    if not (title_element and provider_element):
                        continue

                    if title_element and provider_element:
                        course_data = {
                            "id": str(uuid.uuid4()),  # Generate a unique ID
                            "title": provider_element.text.strip(),
                            "provider": "Harvard",
                            "detail": 'N/A',
                            "rating": 'N/A',
                            "category": title_element.text.strip(),
                            "link": link_href,
                            "image": img_url
                        }
                        courses_list.append(course_data)

                except Exception as e:
                    self.logger.error(f"Error parsing Harvard course: {str(e)}")
                    continue

            # self.logger.info(f"Fetched {len(courses_list)} Harvard courses")
            return courses_list
        else:
            self.logger.error("Failed to fetch Harvard courses")
            return []