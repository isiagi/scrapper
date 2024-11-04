from flask import Flask, jsonify
from flask_cors import CORS
import random
from flask_caching import Cache
from flask_apscheduler import APScheduler
import os
from course_scaper import Scraper

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


# API endpoint to return all courses with caching
@app.route('/api/courses', methods=['GET'])
@cache.cached(timeout=86400)  # Cache the result for 24 hours
def get_courses():
    scraper = Scraper()
    coursera_courses = scraper.scrape_coursera()
    harvard_courses = scraper.scrape_harvard_courses()

    # Combine all courses into one list and shuffle
    all_courses = coursera_courses + harvard_courses
    random.shuffle(all_courses)

    return jsonify(all_courses)


# clear cache
@app.route('/api/clear_cache', methods=['GET'])
def clear_cache():
    cache.clear()
    return jsonify({'message': 'Cache cleared'})

# Schedule the task to run periodically (e.g., every day at 02:00 AM)
@scheduler.task('interval', id='scheduled_scraping', hours=24)
def scheduled_task():
    get_courses()

if __name__ == '__main__':
    app.run(debug=True)