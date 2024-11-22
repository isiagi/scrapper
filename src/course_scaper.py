import requests
from bs4 import BeautifulSoup
import random
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
import re



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
    def scrape_Life_courses(self):
        """Scrape courses from Life's online course catalog"""
        courses_list = []
        URL = 'https://www.life-global.org/allcourses'
        response = self._make_request(URL)

        if not response:
            self.logger.error("Failed to fetch Life courses")
            return []

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            course_containers = soup.find_all('span', class_='ui-core-emotion-cache-4233sn')
            
            self.logger.info(f"Found {len(course_containers)} potential course containers")

            for container in course_containers:
                try:
                    # Extract course title
                    title_element = container.find('h2', class_='ui-core-emotion-cache-1k10co')
                    
                    # Extract course link from the span's href attribute
                    course_link = container.get('href', '')
                    
                    # Extract description
                    description = container.find('p', class_='ui-core-emotion-cache-1yh6jjn')
                    
                    # Extract enrollment count
                    enrollment_element = container.find('p', class_='ui-core-emotion-cache-1h70fjn')
                    
                    # Extract image URL - specifically targeting the noscript img with data-nimg="fill"
                    noscript_element = container.find('noscript')
                    img_url = None
                    if noscript_element:
                        img_tag = noscript_element.find('img', attrs={'data-nimg': 'fill'})
                        if img_tag and 'src' in img_tag.attrs:
                            # Extract the base image URL from the src attribute
                            img_src = img_tag['src']
                            if img_src.startswith('/_next/image'):
                                img_url = f"https://www.life-global.org{img_src}"

                    # Skip if required elements are missing
                    if not title_element:
                        self.logger.warning("Skipping course - missing title element")
                        continue

                    course_data = {
                        "id": str(uuid.uuid4()),
                        "title": title_element.text.strip() if title_element else 'N/A',
                        "provider": "Life HP",
                        "detail": description.text.strip() if description else 'N/A',
                        "enrollment": enrollment_element.text.strip() if enrollment_element else 'N/A',
                        "link": f"https://www.life-global.org{course_link}" if course_link else 'N/A',
                        "image": img_url if img_url else 'N/A'
                    }

                    self.logger.debug(f"Parsed course: {course_data['title']}")
                    courses_list.append(course_data)

                except Exception as e:
                    self.logger.error(f"Error parsing individual course: {str(e)}")
                    continue

            self.logger.info(f"Successfully scraped {len(courses_list)} Life courses")
            return courses_list

        except Exception as e:
            self.logger.error(f"Error during Life courses scraping: {str(e)}")
            return []
        
    def scrape_who_courses(self):
        """Scrape courses from WHO online course catalog"""
        courses_list = []
        URL = 'https://openwho.org/courses?q=&channel=&lang=&category=&topic='
        response = self._make_request(URL)

        if not response:
            self.logger.error("Failed to fetch WHO courses")
            return []

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            course_containers = soup.find_all('div', class_='course-card course-card--expandable')
            
            self.logger.info(f"Found WHO {len(course_containers)} potential course containers")

            for container in course_containers:
                try:
                    # Extract course title and link
                    title_element = container.find('div', class_='course-card__title').find('a')
                    course_link = title_element.get('href') if title_element else None
                    
                    # Extract description
                    description = container.find('div', class_='course-card__description').find('p')
                    
                    # Extract provider
                    provider = container.find('div', class_='course-card__teacher')
                    
                    # Extract course date/type
                    date_element = container.find('li', class_='course-card__date').find('span', class_='xi-icon').find_next_sibling('span')
                    
                    # Extract language
                    language_element = container.find('li', class_='course-card__language').find('span', class_='xi-icon').find_next_sibling('span')
                    
                    # Extract certificate type
                    certificate_element = container.find('li', class_='course-card__certificates').find('span', class_='xi-icon').find_next_sibling('span')
                    
                    # Extract image URL from the picture element's img tag
                    img_element = container.find('picture').find('img')
                    img_url = img_element.get('src') if img_element else None

                    # Skip if required elements are missing
                    if not title_element:
                        self.logger.warning("Skipping course - missing title element")
                        continue

                    course_data = {
                        "id": str(uuid.uuid4()),
                        "title": title_element.text.strip() if title_element else 'N/A',
                        "provider": provider.text.strip() if provider else 'WHO',
                        "detail": description.text.strip() if description else 'N/A',
                        "course_type": date_element.text.strip() if date_element else 'N/A',
                        "language": language_element.text.strip() if language_element else 'N/A',
                        "certificate": certificate_element.text.strip() if certificate_element else 'N/A',
                        "link": f"https://openwho.org{course_link}" if course_link else 'N/A',
                        "image": img_url if img_url else 'N/A'
                    }

                    self.logger.debug(f"Parsed WHO course: {course_data['title']}")
                    courses_list.append(course_data)

                except Exception as e:
                    self.logger.error(f"Error parsing individual WHO course: {str(e)}")
                    continue

            self.logger.info(f"Successfully scraped {len(courses_list)} WHO courses")
            return courses_list

        except Exception as e:
            self.logger.error(f"Error during WHO courses scraping: {str(e)}")
            return []
        
    # def scrape_udacity_courses(self):
    #     """Scrape courses from Udacity's online course catalog"""
    #     courses_list = []
    #     URL = 'https://www.classcentral.com/provider/udacity?free=true'
        
    #     try:
    #         response = self._make_request(URL)
    #         if not response:
    #             self.logger.error("Failed to fetch Udacity courses")
    #             return []

    #         soup = BeautifulSoup(response.text, 'html.parser')
    #         course_items = soup.find_all('li', class_='course-list-course')

    #         def extract_image_url(course_item):
    #             """Extract the course image URL with multiple fallback strategies."""
    #             # Try to find an image within the <picture> tag
    #             img = course_item.find('picture')
    #             # print(img)
    #             if img:
    #                 # Check for 'img' tag inside <picture>
    #                 # img_tag = img.find('img')
    #                 # if img_tag and img_tag.get('src'):
    #                 #     return img_tag['src']
                    
    #                 # Check for 'source' tag with 'srcset' attribute inside <picture>
    #                 source_tag = img.find('source')
    #                 if source_tag and source_tag.get('srcset'):
    #                     try:
    #                         # Split the srcset into multiple URLs and take the last one
    #                         last_srcset_item = source_tag['srcset'].split(',')[0]
    #                         # Further split by space to get just the URL
    #                         image_url = last_srcset_item.split()[0]
    #                         return image_url
    #                     except (IndexError, AttributeError):
    #                     # Return a fallback image or 'N/A' if there's an issue
    #                      return 'https://ccweb.imgix.net/https%3A%2F%2Fwww.classcentral.com%2Fimages%2Flogos%2Fproviders%2Fudemy-hz.png?auto=format&ixlib=php-4.1.0&s=4e8ff3b5ec79b25af845d12fed93431b'
    #                 # If 'srcset' attribute is not found, return the first URL in 'srcset'
    #                     # return source_tag['srcset'].split(',')[0].split()[2]  # Use first URL in srcset
                    
    #             # Fallback: check if there's any 'img' tag directly inside the course item
    #             fallback_img = course_item.find('img')
    #             if fallback_img and fallback_img.get('src'):
    #                 return fallback_img['src']
                
    #             # If all fails, return a placeholder or indicate missing image
    #             return 'https://ccweb.imgix.net/https%3A%2F%2Fwww.classcentral.com%2Fimages%2Flogos%2Fproviders%2Fudemy-hz.png?auto=format&ixlib=php-4.1.0&s=4e8ff3b5ec79b25af845d12fed93431b'
            

    #         def clean_udacity_url(url):
    #             """Clean Udemy course URL by removing 'udemy-' prefix and numeric suffix.
                
    #             Args:
    #                 url (str): The original Udemy course URL
                    
    #             Returns:
    #                 str: Cleaned URL with prefix and suffix removed
    #             """
    #             try:
    #                 # Split the URL to get the course slug
    #                 parts = url.split('/course/')
    #                 if len(parts) != 2:
    #                     return url
                        
    #                 base_url = parts[0]
    #                 course_slug = parts[1]
                    
    #                 # Remove the numeric suffix (e.g., -25803)
    #                 course_slug = re.sub(r'-\d+/?$', '', course_slug)
                    
    #                 # Remove 'udemy-' prefix from the course slug
    #                 if course_slug.startswith('udacity-'):
    #                     course_slug = course_slug[6:]
                        
    #                 # Reconstruct the URL
    #                 return f"{base_url}/course/{course_slug}"
    #             except:
    #                 return url

    #         for course_item in course_items:
    #             try:
    #                 # Extract course details
    #                 title_element = course_item.find('h2', class_='text-1')
    #                 link_element = course_item.find('a', class_='course-name')
    #                 detail_element = course_item.find('p', class_='text-2')
    #                 rating_element = course_item.find('span', class_='cmpt-rating-medium')
    #                 image_element = course_item.find('picture').find('img')

    #                 # print(image_element, '===test====')
                    
    #                 course_data = {
    #                     "id": str(uuid.uuid4()),
    #                     "title": title_element.text.strip() if title_element else 'N/A',
    #                     "provider": "Udacity",
    #                     "link": clean_udacity_url("https://www.udacity.com" + link_element.get('href', 'N/A')) if link_element else 'N/A',
    #                     "detail": detail_element.text.strip() if detail_element else 'N/A',
    #                     "rating": len(rating_element.find_all('i', class_='icon-star')) if rating_element else 'N/A',
    #                     "category": 'N/A',
    #                     "image": extract_image_url(course_item)
    #                 }
    #                 # print(course_data)
    #                 courses_list.append(course_data)

    #             except Exception as e:
    #                 self.logger.error(f"Error parsing Udacity course: {str(e)}")
    #                 continue

    #         self.logger.info(f"Fetched {len(courses_list)} Udacity courses")
    #         # print(courses_list)
    #         return courses_list

    #     except Exception as e:
    #         self.logger.error(f"Error in scraping Udacity courses: {str(e)}")
    #         return []
        

    def scrape_udemy_courses(self):
        """Scrape courses from Udemy's online course catalog"""
        courses_list = []
        URL = 'https://www.classcentral.com/provider/udemy?free=true'
        
        try:
            response = self._make_request(URL)
            if not response:
                self.logger.error("Failed to fetch Udacity courses")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            course_items = soup.find_all('li', class_='course-list-course')

            def extract_image_url(course_item):
                """Extract the course image URL with multiple fallback strategies."""
                # Try to find an image within the <picture> tag
                img = course_item.find('picture')
                # print(img)
                if img:
                    # Check for 'img' tag inside <picture>
                    # img_tag = img.find('img')
                    # if img_tag and img_tag.get('src'):
                    #     return img_tag['src']
                    
                    # Check for 'source' tag with 'srcset' attribute inside <picture>
                    source_tag = img.find('source')
                    if source_tag and source_tag.get('srcset'):
                        try:
                            # Split the srcset into multiple URLs and take the last one
                            last_srcset_item = source_tag['srcset'].split(',')[0]
                            # Further split by space to get just the URL
                            image_url = last_srcset_item.split()[0]
                            return image_url
                        except (IndexError, AttributeError):
                        # Return a fallback image or 'N/A' if there's an issue
                         return 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRyHXDWa_y17Bn3eVyMhDOizFfK3o0eJFyyiw&s'
                    # If 'srcset' attribute is not found, return the first URL in 'srcset'
                        # return source_tag['srcset'].split(',')[0].split()[2]  # Use first URL in srcset
                    
                # Fallback: check if there's any 'img' tag directly inside the course item
                fallback_img = course_item.find('img')
                if fallback_img and fallback_img.get('src'):
                    return fallback_img['src']
                
                # If all fails, return a placeholder or indicate missing image
                return 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRyHXDWa_y17Bn3eVyMhDOizFfK3o0eJFyyiw&s'
            def clean_udemy_url(url):
                """Clean Udemy course URL by removing 'udemy-' prefix and numeric suffix.
                
                Args:
                    url (str): The original Udemy course URL
                    
                Returns:
                    str: Cleaned URL with prefix and suffix removed
                """
                try:
                    # Split the URL to get the course slug
                    parts = url.split('/course/')
                    if len(parts) != 2:
                        return url
                        
                    base_url = parts[0]
                    course_slug = parts[1]
                    
                    # Remove the numeric suffix (e.g., -25803)
                    course_slug = re.sub(r'-\d+/?$', '', course_slug)
                    
                    # Remove 'udemy-' prefix from the course slug
                    if course_slug.startswith('udemy-'):
                        course_slug = course_slug[6:]
                        
                    # Reconstruct the URL
                    return f"{base_url}/course/{course_slug}"
                except:
                    return url

            for course_item in course_items:
                try:
                    # Extract course details
                    title_element = course_item.find('h2', class_='text-1')
                    link_element = course_item.find('a', class_='course-name')
                    detail_element = course_item.find('p', class_='text-2')
                    rating_element = course_item.find('span', class_='cmpt-rating-medium')
                    image_element = course_item.find('picture').find('img')

                    # print(image_element, '===test====')
                    
                    course_data = {
                        "id": str(uuid.uuid4()),
                        "title": title_element.text.strip() if title_element else 'N/A',
                        "provider": "Udemy",
                        "link": clean_udemy_url("https://www.udemy.com" + link_element.get('href', 'N/A')) if link_element else 'N/A',
                        "detail": detail_element.text.strip() if detail_element else 'N/A',
                        "rating": len(rating_element.find_all('i', class_='icon-star')) if rating_element else 'N/A',
                        "category": 'N/A',
                        "image": extract_image_url(course_item)
                    }
                    # print(course_data)
                    courses_list.append(course_data)

                except Exception as e:
                    self.logger.error(f"Error parsing Udacity course: {str(e)}")
                    continue

            self.logger.info(f"Fetched {len(courses_list)} Udacity courses")
            # print(courses_list)
            return courses_list

        except Exception as e:
            self.logger.error(f"Error in scraping Udacity courses: {str(e)}")
            return []