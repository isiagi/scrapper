from flask import Flask, jsonify
from flask_cors import CORS
import random
import logging
from concurrent.futures import ThreadPoolExecutor
import os
from dotenv import load_dotenv

from course_scraper import CourseScraper


load_dotenv()


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    CORS(app)
    scraper = CourseScraper()


    @app.route("/api/courses", methods=["GET"])
    def get_courses():
        try:
           
            # Parallel execution
            with ThreadPoolExecutor(max_workers=2) as executor:
                coursera_future = executor.submit(scraper.get_coursera_courses)
                coursera_courses = coursera_future.result()

                harvard_future = executor.submit(scraper.get_harvard_courses)
                harvard_courses = harvard_future.result()


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
