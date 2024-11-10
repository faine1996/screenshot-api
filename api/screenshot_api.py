from flask import Flask, send_file, jsonify, request
import subprocess
import os
import time
import logging
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

def take_screenshot(url):
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
        
        # Ensure screenshot directory exists
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        
        # Take screenshot
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'screenshot_{timestamp}.png'
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        logger.debug(f"Saving screenshot to {filepath}")
        driver.save_screenshot(filepath)
        
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            logger.debug(f"Screenshot saved successfully. Size: {os.path.getsize(filepath)} bytes")
            return filepath
        else:
            logger.error("Screenshot file not found or empty")
            return None
            
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
        # Check if screenshots directory exists and is writable
        screenshots_dir = Path(SCREENSHOT_DIR)
        if not screenshots_dir.exists():
            screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        if not os.access(SCREENSHOT_DIR, os.W_OK):
            return jsonify({
                "status": "error",
                "message": f"Screenshot directory {SCREENSHOT_DIR} is not writable"
            }), 500
        
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
    """Take a screenshot of the provided URL"""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
        
    url = request.json.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400
        
    if not url.startswith(('http://', 'https://')):
        return jsonify({"error": "Invalid URL. Must start with http:// or https://"}), 400
        
    logger.info(f"Screenshot requested for URL: {url}")
    
    # Ensure screenshot directory exists
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    screenshot_path = take_screenshot(url)
    
    if not screenshot_path:
        return jsonify({
            "error": "Failed to take screenshot",
            "details": "The screenshot process failed"
        }), 500
        
    try:
        logger.debug(f"Sending screenshot: {screenshot_path}")
        return send_file(
            screenshot_path,
            mimetype='image/png',
            as_attachment=True,
            download_name=os.path.basename(screenshot_path)
        )
    except Exception as e:
        logger.error(f"Error sending file: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Failed to send screenshot",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    logger.info("Starting API server...")
    # Ensure screenshots directory exists and is writable
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.chmod(SCREENSHOT_DIR, 0o777)  # Make sure directory is writable
    
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