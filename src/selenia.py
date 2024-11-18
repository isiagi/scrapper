from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import logging
import uuid
import time
import random
from typing import List, Dict, Optional
import os
import atexit
from webdriver_manager.chrome import ChromeDriverManager

class UdacityScraper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        self.driver = None
        self.service = None
        self.max_retries = 3
        self.retry_delay = 5
        atexit.register(self.cleanup)

    def setup_logging(self):
        """Configure detailed logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    def cleanup(self):
        """Clean up resources properly"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("WebDriver quit successfully")
            except Exception as e:
                self.logger.error(f"Error during driver cleanup: {str(e)}")
        
        self.driver = None
        self.service = None

    def get_chrome_driver_path(self) -> str:
        """Get the appropriate ChromeDriver path based on the environment"""
        try:
            # First, try using webdriver_manager
            driver_path = ChromeDriverManager().install()
            self.logger.info(f"ChromeDriver installed at: {driver_path}")
            return driver_path
        except Exception as e:
            self.logger.warning(f"Failed to install ChromeDriver using webdriver_manager: {str(e)}")
            
            # Fallback to environment variable
            driver_path = os.environ.get('CHROME_DRIVER_PATH')
            if driver_path and os.path.exists(driver_path):
                self.logger.info(f"Using ChromeDriver from environment variable: {driver_path}")
                return driver_path
            
            # Fallback to common locations
            common_locations = [
                '/usr/local/bin/chromedriver',
                '/usr/bin/chromedriver',
                'C:\\Program Files\\ChromeDriver\\chromedriver.exe',
                'C:\\chromedriver.exe'
            ]
            
            for location in common_locations:
                if os.path.exists(location):
                    self.logger.info(f"Found ChromeDriver at common location: {location}")
                    return location
            
            raise Exception("ChromeDriver not found in any expected location")

    def setup_driver(self) -> bool:
        """Setup Chrome driver with enhanced error handling and proper path configuration"""
        try:
            # Get ChromeDriver path
            driver_path = self.get_chrome_driver_path()
            self.logger.info(f"Using ChromeDriver from path: {driver_path}")
            
            # Initialize service with explicit path
            self.service = Service(executable_path=driver_path)
            
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-setuid-sandbox')
            
            # Add stability-focused options
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-infobars')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--enable-logging')
            chrome_options.add_argument('--log-level=0')
            chrome_options.add_argument('--v=99')
            
            # Add connection stability options
            chrome_options.add_argument('--disable-background-networking')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-breakpad')
            chrome_options.add_argument('--disable-client-side-phishing-detection')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-hang-monitor')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--disable-prompt-on-repost')
            chrome_options.add_argument('--disable-sync')
            
            # Set page load strategy
            chrome_options.page_load_strategy = 'eager'
            
            # Initialize driver with service and options
            self.driver = webdriver.Chrome(service=self.service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            # Verify connection
            self.driver.execute_script('return document.readyState')
            self.logger.info("Chrome WebDriver initialized and verified successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Chrome WebDriver: {str(e)}")
            self.cleanup()
            return False

    def wait_for_element(self, by: By, value: str, timeout: int = 20) -> bool:
        """Enhanced element wait with connection verification"""
        try:
            # Verify driver connection before waiting
            self.driver.execute_script('return document.readyState')
            
            wait = WebDriverWait(self.driver, timeout, poll_frequency=0.5)
            element = wait.until(EC.presence_of_element_located((by, value)))
            
            # Additional checks for element stability
            wait.until(EC.visibility_of(element))
            wait.until(EC.element_to_be_clickable((by, value)))
            
            return True
            
        except TimeoutException:
            self.logger.warning(f"Timeout waiting for element: {value}")
            return False
        except WebDriverException as e:
            if "disconnected" in str(e):
                self.logger.error("WebDriver disconnected, attempting to reconnect...")
                return self.reconnect_and_retry(by, value, timeout)
            self.logger.error(f"WebDriver error waiting for element {value}: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error waiting for element {value}: {str(e)}")
            return False

    def reconnect_and_retry(self, by: By, value: str, timeout: int) -> bool:
        """Attempt to reconnect and retry the operation"""
        try:
            self.cleanup()
            if self.setup_driver():
                self.driver.get(self.driver.current_url)
                return self.wait_for_element(by, value, timeout)
            return False
        except Exception as e:
            self.logger.error(f"Reconnection attempt failed: {str(e)}")
            return False

    def scroll_page(self, scroll_pause: float = 2.0) -> None:
        """Improved page scrolling with connection verification"""
        try:
            # Verify connection before scrolling
            self.driver.execute_script('return document.readyState')
            
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scrolls = 0
            max_scrolls = 10
            
            while scrolls < max_scrolls:
                # Smooth scrolling with smaller increments
                current_position = self.driver.execute_script("return window.pageYOffset;")
                target_position = current_position + 300
                
                self.driver.execute_script(f"""
                    window.scrollTo({{
                        top: {target_position},
                        behavior: 'smooth'
                    }});
                """)
                
                time.sleep(scroll_pause)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    self.logger.info("Reached end of page")
                    break
                    
                last_height = new_height
                scrolls += 1
                self.logger.debug(f"Completed scroll {scrolls}/{max_scrolls}")
                
        except WebDriverException as e:
            if "disconnected" in str(e):
                self.logger.error("Disconnected during scrolling, attempting to reconnect...")
                self.reconnect_and_retry(By.TAG_NAME, "body", 20)
            else:
                self.logger.error(f"WebDriver error during scrolling: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error during page scrolling: {str(e)}")

    def scrape_udacity_courses(self) -> List[Dict]:
        """Enhanced main scraping function with better error handling"""
        courses_list = []
        base_url = 'https://www.udemy.com/courses/free/'
        attempt = 0
        
        while attempt < self.max_retries:
            try:
                if not self.setup_driver():
                    raise Exception("Failed to initialize WebDriver")
                
                self.logger.info(f"Scraping attempt {attempt + 1}/{self.max_retries}")
                
                # Load page with retry mechanism
                load_success = False
                load_attempts = 3
                for _ in range(load_attempts):
                    try:
                        self.driver.get(base_url)
                        self.driver.execute_script('return document.readyState')
                        load_success = True
                        break
                    except Exception as e:
                        self.logger.warning(f"Page load attempt failed: {str(e)}")
                        time.sleep(2)
                
                if not load_success:
                    raise Exception("Failed to load page after multiple attempts")
                
                self.logger.info("Loaded catalog page")
                
                # Wait for initial content with increased timeout
                if not self.wait_for_element(By.CLASS_NAME, "course-list_container__yXli8", timeout=30):
                    raise TimeoutException("Course container not found")
                
                # Scroll with improved stability
                self.scroll_page(scroll_pause=3.0)
                
                # Parse courses with retry mechanism
                for parse_attempt in range(3):
                    courses_list = self.parse_courses(self.driver.page_source)
                    if courses_list:
                        break
                    time.sleep(2)
                
                if not courses_list:
                    raise Exception("No courses found after parsing")
                
                self.logger.info(f"Successfully scraped {len(courses_list)} courses")
                break
                
            except Exception as e:
                attempt += 1
                self.logger.error(f"Attempt {attempt} failed: {str(e)}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)  # Exponential backoff
            finally:
                self.cleanup()
                
        return courses_list