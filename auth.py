import os
import logging
import requests
import threading
from datetime import datetime, timedelta
from steps import step

# Thread-safe token storage
_token_lock = threading.Lock()
_auth_token = None
_token_expiry = None


def _load_credentials():
    """Load API credentials from environment variables."""
    login_url = os.environ.get("API_LOGIN_URL", "")
    username = os.environ.get("API_EMAIL", "")
    password = os.environ.get("API_PASSWORD", "")
    
    if not login_url or not username or not password:
        raise ValueError("API_LOGIN_URL, API_EMAIL and API_PASSWORD environment variables must be set")
    
    return login_url, username, password


def login():
    """Login to API and get authentication token.
    
    Returns:
        str: Authentication token on success
        None: If login fails
    """
    global _auth_token, _token_expiry
    
    try:
        login_url, username, password = _load_credentials()
        
        step(f"Authenticating with API: {login_url}")
        
        response = requests.post(
            login_url,
            json={"login": username, "password": password},
            timeout=10,
            verify=False  # Disable SSL verification for UAT environment
        )
        
        if response.status_code == 200:
            data = response.json()
            logging.info(f"Login response structure: {list(data.keys())}")
            
            # The API returns token in a nested structure: {"token": {"accessToken": "...", "tokenType": "Bearer"}}
            token_obj = data.get("token", {})
            
            # Extract the actual access token string
            if isinstance(token_obj, dict):
                token = token_obj.get("accessToken")
            else:
                token = token_obj
            
            if not token:
                raise ValueError(f"No accessToken in login response: {data}")
            
            with _token_lock:
                _auth_token = token
                # Assume token expires in 24 hours if not specified
                expires_in = (data.get("expires_in") or 
                             data.get("expiresIn") or 
                             data.get("expiry") or 
                             86400)
                _token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            step(f"Successfully authenticated. Token expires at {_token_expiry}")
            logging.info(f"✔ API Login successful - Token expires: {_token_expiry}")
            return token
        else:
            error_msg = f"Login failed with status {response.status_code}: {response.text}"
            step(error_msg)
            logging.error(error_msg)
            return None
            
    except Exception as e:
        error_msg = f"Login error: {str(e)}"
        step(error_msg)
        logging.exception(error_msg)
        return None


def get_valid_token():
    """Get a valid authentication token, login if needed or expired.
    
    Returns:
        str: Valid authentication token
        None: If unable to obtain token
    """
    global _auth_token, _token_expiry
    
    with _token_lock:
        # Check if token exists and is still valid
        if _auth_token and _token_expiry and datetime.now() < _token_expiry:
            return _auth_token
    
    # Token missing or expired, login again
    step("Token expired or missing, re-authenticating...")
    return login()


def logout():
    """Clear stored token (optional cleanup on shutdown)."""
    global _auth_token, _token_expiry
    
    with _token_lock:
        _auth_token = None
        _token_expiry = None
    
    logging.info("Logged out - token cleared")


def get_auth_headers():
    """Get HTTP headers with authentication token.
    
    Returns:
        dict: Headers dict with Authorization header
    """
    token = get_valid_token()
    if not token:
        return {}
    
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
