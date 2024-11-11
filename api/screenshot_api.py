from flask import Flask, send_file, jsonify, request, Response
import subprocess
import os
import time
import logging
import io
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

SCREENSHOT_DIR = '/vm/screenshots'

def get_chrome_options():
    """Configure Chrome options"""
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--remote-debugging-port=9222')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    chrome_options.binary_location = '/usr/bin/chromium'
    return chrome_options

def take_screenshot(url, save_file=False):
    """Take a screenshot using Chrome headless"""
    logger.debug(f"Taking screenshot of {url}")
    
    try:
        chrome_options = get_chrome_options()
        service = Service('/usr/bin/chromedriver')
        
        logger.debug("Starting Chrome...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.set_page_load_timeout(30)
        
        logger.debug("Loading page...")
        driver.get(url)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        
        # Additional wait for dynamic content
        time.sleep(2)
        
        # Get screenshot as PNG bytes
        png_data = driver.get_screenshot_as_png()
        
        if save_file:
            # Ensure screenshot directory exists
            os.makedirs(SCREENSHOT_DIR, exist_ok=True)
            
            # Save screenshot
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'screenshot_{timestamp}.png'
            filepath = os.path.join(SCREENSHOT_DIR, filename)
            
            logger.debug(f"Saving screenshot to {filepath}")
            with open(filepath, 'wb') as f:
                f.write(png_data)
        
        return png_data
            
    except Exception as e:
        logger.error(f"Screenshot error: {str(e)}", exc_info=True)
        return None
    finally:
        if 'driver' in locals():
            driver.quit()

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Screenshot API is running"})

@app.route('/ping', methods=['GET'])
def ping():
    return "pong"

@app.route('/status', methods=['GET'])
def status():
    """Check if the API and VM are ready"""
    logger.debug("Status check received")
    try:
        response = jsonify({
            "status": "ready",
            "message": "API is running",
            "time": datetime.now().isoformat()
        })
        
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/screenshot', methods=['POST'])
def screenshot():
    """Take a screenshot of the provided URL and return as PNG"""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
        
    url = request.json.get('url')
    save_file = request.json.get('save_file', False)  # Optional parameter to save file
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
        
    if not url.startswith(('http://', 'https://')):
        return jsonify({"error": "Invalid URL. Must start with http:// or https://"}), 400
        
    logger.info(f"Screenshot requested for URL: {url}")
    
    png_data = take_screenshot(url, save_file)
    
    if not png_data:
        return jsonify({
            "error": "Failed to take screenshot",
            "details": "The screenshot process failed"
        }), 500
        
    try:
        return Response(
            png_data,
            mimetype='image/png',
            headers={
                'Content-Disposition': 'inline',
                'Access-Control-Allow-Origin': '*'
            }
        )
    except Exception as e:
        logger.error(f"Error sending file: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Failed to send screenshot",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    logger.info("Starting API server...")
    
    # Configure Flask app
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.config['PROPAGATE_EXCEPTIONS'] = True
    
    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        threaded=True,
        use_reloader=False
    )