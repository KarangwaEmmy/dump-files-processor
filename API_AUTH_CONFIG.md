# API Authentication Configuration

This application uses token-based authentication to send inspection data to your API. Tokens are managed automatically with automatic re-authentication when expired.

## Configuration (.env file)

```env
HOST_DUMP_DIR=/mnt/c/Dump

# API Configuration
API_URL=https://your-api-domain.com
API_USERNAME=your_api_username
API_PASSWORD=your_api_password
```

### Required Environment Variables
- **API_URL**: Base URL of your API (e.g., `https://api.example.com`)
- **API_USERNAME**: Username for API authentication
- **API_PASSWORD**: Password for API authentication

## Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Application Start                                           │
├─────────────────────────────────────────────────────────────┤
│ 1. main.py calls login()                                    │
│ 2. Sends credentials to API_URL/auth/login                 │
│ 3. Receives token (expires in 24 hours by default)         │
│ 4. Stores token in memory with expiry time                 │
│ 5. Starts file monitoring                                  │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Processing Dump Files                                       │
├─────────────────────────────────────────────────────────────┤
│ 1. File detected in C:\Dump                                │
│ 2. get_valid_token() checks token expiry                   │
│ 3. If valid: use existing token                            │
│ 4. If expired: automatically login() again                 │
│ 5. Send payload with Bearer token in Authorization header  │
│ 6. On success (200/201): Move to processed/               │
│ 7. On 401 Unauthorized: Re-login and retry once           │
│ 8. On failure: Retry 3 times, then move to .failed/       │
└─────────────────────────────────────────────────────────────┘
```

## API Endpoints Expected

The application expects your API to have these endpoints:

### Login Endpoint
```
POST /auth/login

Request:
{
  "username": "your_api_username",
  "password": "your_api_password"
}

Response (200 OK):
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 86400  // Optional: seconds until expiry (default 24h)
}
```

### Data Submission Endpoint
```
POST /inspections

Headers:
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

Request Body:
{
  "inspectionReference": "MAHA-20260120-0815",
  "inspectionDate": "2026-01-20T08:15:00Z",
  "source": "MAHA",
  "inspectorName": "Hassan Ali",
  "inspectionTime": "08:15",
  "plateNumber": "TEST001",
  "ChassisNo": "VIN000000000TEST001",
  "manufacturer": "FORD",
  "vehicleYype": "TRUCK",
  "axleCount": 6,
  "laneNumber": "Lane5",
  "overallResult": "PASS",
  "inspectionResults": [
    {
      "code": "10100",
      "value": "TEST001",
      "testCategory": "Vehicle Identification"
    },
    ...
  ]
}

Response (200/201):
{
  "success": true,
  "inspectionId": "12345"
}
```

## Token Management

### Token Lifecycle
1. **Obtained at startup**: First login happens in `main.py`
2. **Stored in memory**: Token kept in `auth.py` with thread-safe locking
3. **Checked before each request**: `get_valid_token()` verifies expiry
4. **Auto-refreshed when expired**: Automatic re-login when time expires
5. **Cleared on 401**: Manually re-login if server returns 401 Unauthorized

### Token Expiry Handling
```
Token Expiry Time                Current Time
     ↓                                ↓
2026-01-21 08:15:00 ────────────► 2026-01-21 08:10:00
  Still valid                      Token OK, use it
  
  Token OK, use it

2026-01-21 08:15:00 ◄────────────  2026-01-21 08:20:00
  Token expired                     Call login() again
```

### Automatic Re-authentication
The system automatically handles:
- **Expired tokens**: Re-login when token time passes
- **401 Unauthorized**: One retry with fresh login
- **Network failures**: Log error, retry on next file
- **Invalid credentials**: Log critical error, require manual restart with updated .env

## Troubleshooting

### Login Fails at Startup
```
Error: API_USERNAME and API_PASSWORD environment variables not set
Solution: Update .env with correct credentials
```

### 401 Unauthorized During Processing
```
Log: "Token expired (401 Unauthorized), attempting re-authentication..."
Action: System automatically re-logins and retries
```

### Token Never Obtained
```
Check:
1. API_URL is correct and reachable
2. API_USERNAME and API_PASSWORD are correct
3. API /auth/login endpoint exists and works
4. Network connectivity to API server
5. Docker logs: docker-compose logs dump_listener
```

### Files Not Processed
```
Likely cause: Authentication failure
Check logs for:
- "Failed to obtain authentication token"
- "Login error:" messages
- API connectivity issues

Verify in logs:
docker-compose logs dump_listener | grep -i "auth\|login"
```

## Examples

### Test Authentication Manually (from host)
```bash
# Test API login
curl -X POST https://your-api-domain.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"your_username","password":"your_password"}'

# Should return token:
# {"token":"eyJhbGciOiJIUzI1NiIs...","expires_in":86400}
```

### Monitor Authentication in Logs
```bash
# Watch for login attempts
docker-compose logs -f dump_listener | grep -i "login\|auth\|token"

# View successful auth
docker-compose logs dump_listener | grep "Successfully authenticated"

# View token expiry
docker-compose logs dump_listener | grep "Token expires"
```

### Update Credentials Without Restart
1. Edit `.env` file with new credentials
2. Rebuild container: `docker-compose up -d --build`
3. Old token is discarded, new login happens automatically

## Security Notes

- **Credentials in .env**: Git-ignore this file (add to .gitignore)
- **Token in memory**: Lives only in running container process
- **Token not logged**: Token value never printed to logs
- **HTTPS only**: Always use HTTPS (not HTTP) for API_URL
- **Token expiry**: Default 24 hours, adjust API settings if needed

## Support

For authentication issues:
1. Check `.env` file has correct API_URL, username, password
2. Test API login endpoint manually with curl
3. Review logs: `docker-compose logs dump_listener`
4. Ensure API server is running and accessible
5. Verify firewall allows connection to API server
