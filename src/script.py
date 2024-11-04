from flask import Flask, jsonify, request
from flask_cors import CORS
import random
from flask_caching import Cache
from flask_apscheduler import APScheduler
import os
from course_scaper import Scraper
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
    with ThreadPoolExecutor(max_workers=2) as executor:
        coursera_future = executor.submit(scraper.scrape_coursera)
        harvard_future = executor.submit(scraper.scrape_harvard_courses)
        
        coursera_courses = coursera_future.result()
        harvard_courses = harvard_future.result()
        
        all_courses = coursera_courses + harvard_courses
        random.shuffle(all_courses)
        
        # Store in cache for 24 hours
        cache.set(cache_key, all_courses, timeout=86400)
        
        return jsonify(all_courses)

def run_background_scraping():
    def background_scrape():
        scraper = Scraper()
        with ThreadPoolExecutor(max_workers=2) as executor:
            coursera_future = executor.submit(scraper.scrape_coursera)
            harvard_future = executor.submit(scraper.scrape_harvard_courses)
            
            coursera_courses = coursera_future.result()
            harvard_courses = harvard_future.result()
            
            all_courses = coursera_courses + harvard_courses
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
        
        response = requests.get('https://flask-redis-app.onrender.com/api/courses')
        print(f"Keep-alive ping status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Keep-alive ping failed: {e}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)