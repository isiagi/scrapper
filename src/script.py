import sys
sys.path.append('src')

from flask import Flask, jsonify, request
from flask_cors import CORS
import random
from flask_caching import Cache
from flask_apscheduler import APScheduler
import os
from course_scaper import Scraper
# from selenia import UdacityScraper
import threading
from concurrent.futures import ThreadPoolExecutor
import requests  

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

# API endpoint to return all courses with caching
@app.route('/api/courses', methods=['GET'])
def get_courses():
    # Generate a cache key based on relevant parameters
    cache_key = 'courses_data'
    
    # Try to get data from cache first
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return jsonify(cached_data)
    
    # If not in cache, fetch and store the data
    scraper = Scraper()
    # udacity_scraper = UdacityScraper()
    with ThreadPoolExecutor(max_workers=4) as executor:
        coursera_future = executor.submit(scraper.scrape_coursera)
        harvard_future = executor.submit(scraper.scrape_harvard_courses)
        # udacity_future = executor.submit(scraper.scrape_udacity_courses)
        udemy_future = executor.submit(scraper.scrape_udemy_courses)
        life_future = executor.submit(scraper.scrape_Life_courses)
        who_future = executor.submit(scraper.scrape_who_courses)
        
        coursera_courses = coursera_future.result()
        harvard_courses = harvard_future.result()
        # udacity_courses = udacity_future.result()
        udemy_courses = udemy_future.result()
        life_courses = life_future.result()
        who_courses = who_future.result()
        
        # print(f"Coursera courses: {len(coursera_courses)}")
        # print(f"Harvard courses: {len(harvard_courses)}")
        # print(f"Udacity courses: {len(udacity_courses)}")
        # print(f"Udemy courses: {len(udemy_courses)}")
        print(f"Life courses: {len(life_courses)}")
        print(f"WHO courses: {len(who_courses)}")
        
        # Concatenate all fetched courses

        # print(f"Coursera courses: {len(coursera_courses)}")
        # print(f"Harvard courses: {len(harvard_courses)}")
        # print(f"Udemy courses: {len(udemy_courses)}")
        
        all_courses = coursera_courses + harvard_courses + udemy_courses + life_courses + who_courses
        # print(f"All courses: {len(all_courses)}")
        random.shuffle(all_courses)
        
        # Store in cache for 24 hours
        cache.set(cache_key, all_courses, timeout=86400)
        
        return jsonify(all_courses)

def run_background_scraping():
    def background_scrape():
        scraper = Scraper()
        # udemy_scraper = UdemyCourseScraper(logger=scraper.logger)
        # udacity_scraper = UdacityScraper()
        with ThreadPoolExecutor(max_workers=4) as executor:
            coursera_future = executor.submit(scraper.scrape_coursera)
            harvard_future = executor.submit(scraper.scrape_harvard_courses)
            # udacity_future = executor.submit(scraper.scrape_udacity_courses)
            udemy_future = executor.submit(scraper.scrape_udemy_courses)
            life_future = executor.submit(scraper.scrape_Life_courses)
            who_future = executor.submit(scraper.scrape_who_courses)
            
            coursera_courses = coursera_future.result()
            harvard_courses = harvard_future.result()
            # udacity_courses = udacity_future.result()
            udemy_courses = udemy_future.result()
            life_courses = life_future.result()
            who_courses = who_future.result()
            
            # print(f"Coursera courses: {len(coursera_courses)}")
            # print(f"Harvard courses: {len(harvard_courses)}")
            # print(f"Udacity courses: {len(udacity_courses)}")
            # print(f"Udemy courses: {len(udemy_courses)}")
            print(f"Life courses: {len(life_courses)}")
            print(f"WHO courses: {len(who_courses)}")
            
            # Concatenate all fetched courses
            
            all_courses = coursera_courses + harvard_courses + udemy_courses + life_courses + who_courses
            random.shuffle(all_courses)
            
            # Update the cache with new data
            cache.set('courses_data', all_courses, timeout=86400)
    
    thread = threading.Thread(target=background_scrape)
    thread.daemon = True  # Make thread daemon so it exits when main program exits
    thread.start()

@app.route('/api/clear_cache', methods=['GET'])
def clear_cache():
    cache.clear()
    return jsonify({'message': 'Cache cleared'})

@scheduler.task('interval', id='scheduled_scraping', hours=24)
def scheduled_task():
    run_background_scraping()

# New scheduler task to keep the service alive
@scheduler.task('interval', id='keep_alive', minutes=14)
def keep_service_alive():
    try:
        
        response = requests.get('https://free-course-hive.onrender.com/api/courses')
        print(f"Keep-alive ping status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Keep-alive ping failed: {e}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
