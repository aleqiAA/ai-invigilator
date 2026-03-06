# Login Debug - Browser Issues

## Test Results (Automated)
✅ Login works correctly with test client
✅ CSRF token is generated properly
✅ Session is created with correct role ('invigilator')
✅ Database connection working
✅ Credentials validated correctly

## Possible Browser Issues

### 1. **Cookies Not Being Set**
Check if cookies are enabled in your browser.

### 2. **CSRF Token Mismatch**
The CSRF token might not be submitted correctly.

### 3. **Session Cookie SameSite Issue**
Chrome blocks cookies without Secure flag on localhost.

### 4. **Browser Cache**
Old session data might be interfering.

## Solutions

### Quick Fix - Clear Browser Data
1. Press `Ctrl + Shift + Delete`
2. Clear cookies and cache
3. Restart browser
4. Try again

### Fix Session Cookie Settings

Edit `.env`:
```
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
```

Then restart the app.

### Test in Incognito/Private Mode
Open browser in incognito mode and try:
- URL: http://localhost:5000/login/invigilator
- Email: johndoe@gmail.com
- Password: password123

### Check Browser Console
1. Press `F12` to open DevTools
2. Go to Console tab
3. Look for errors (red text)
4. Share any errors you see

### Check Application Logs
Run the app and watch for errors:
```bash
cd "c:\Users\alexn\OneDrive\python file schol\ai_invigilator"
python app.py
```

Then check `logs/ai_invigilator.log` if it exists.

## Alternative: Test with curl

```bash
# Get CSRF token
curl -c cookies.txt http://localhost:5000/login/invigilator

# Login
curl -X POST http://localhost:5000/login/invigilator ^
  -d "email=johndoe@gmail.com" ^
  -d "password=password123" ^
  -d "csrf_token=YOUR_TOKEN_FROM_PAGE" ^
  -b cookies.txt -c cookies.txt ^
  -L -v
```

## Most Likely Issue: Browser Cache

The most common issue is browser cache. Try:
1. `Ctrl + F5` (hard refresh)
2. Or open in Incognito: `Ctrl + Shift + N` (Chrome) or `Ctrl + Shift + P` (Firefox)
