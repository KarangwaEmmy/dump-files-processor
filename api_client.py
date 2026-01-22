import logging
import os
import time
import requests
from steps import step
from auth import get_auth_headers, get_valid_token, login

# Disable SSL warnings for UAT environment
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def send_to_api(payload):
    """Send payload to API with authentication. Return True on success, False on failure.
    
    Handles:
    - Automatic login on first call
    - Token refresh on expiration
    - Retry logic with re-authentication on 401 Unauthorized
    """
    try:
        api_url = os.environ.get("API_URL", "").rstrip("/")
        
        if not api_url:
            step("API_URL not configured in environment")
            logging.error("API_URL environment variable not set")
            return False
        
        # Ensure we have a valid token before attempting to send
        if not get_valid_token():
            step("Failed to obtain authentication token - aborting API send")
            logging.error("No valid authentication token available")
            return (False, "No valid authentication token available")
        
        step("Sending data to API...")
        step(f"Payload: {payload}")
        
        # API endpoint is the base URL itself (already includes /maha path)
        api_endpoint = api_url
        
        headers = get_auth_headers()
        if not headers:
            step("Failed to get authentication headers")
            return False
        
        response = requests.post(
            api_endpoint,
            json=payload,
            headers=headers,
            timeout=10,
            verify=False  # Disable SSL verification for UAT environment
        )
        
        # Handle 401 Unauthorized - token may have expired
        if response.status_code == 401:
            step("Token expired (401 Unauthorized), attempting re-authentication...")
            logging.warning("Received 401 Unauthorized - re-authenticating")
            
            # Force re-login
            if login():
                # Retry with new token
                headers = get_auth_headers()
                response = requests.post(
                    api_endpoint,
                    json=payload,
                    headers=headers,
                    timeout=10,
                    verify=False
                )
            else:
                step("Re-authentication failed")
                return False
        
        # Check for success
        if response.status_code in (200, 201, 202):
            step("Data sent to API successfully")
            logging.info(f"✔ API response: {response.status_code}")
            print("✔ Data processed and sent successfully")
            return (True, response.text)
        else:
            error_msg = f"API error {response.status_code}: {response.text}"
            step(error_msg)
            logging.error(error_msg)
            # Return tuple with success flag and response text for error handling
            return (False, response.text)
            
    except requests.exceptions.Timeout:
        error_msg = "API request timeout"
        step(error_msg)
        logging.error(error_msg)
        return (False, error_msg)
    except requests.exceptions.ConnectionError as e:
        error_msg = f"API connection error: {str(e)}"
        step(error_msg)
        logging.error(error_msg)
        return (False, error_msg)
    except Exception as e:
        error_msg = f"API error: {str(e)}"
        step(error_msg)
        logging.exception(error_msg)
        return (False, error_msg)
