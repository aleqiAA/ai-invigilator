import sys
import os
import traceback

# Capture all errors to a file
class ErrorCatcher:
    def __init__(self, filename):
        self.filename = filename
        self.file = open(filename, 'w', encoding='utf-8')
    
    def write(self, text):
        self.file.write(text)
        self.file.flush()
        print(text, end='')
    
    def flush(self):
        self.file.flush()

# Redirect stderr to capture errors
sys.stderr = ErrorCatcher('error_output.txt')

try:
    # Import and run the app
    from app import app
    
    print("Starting app with error capture...")
    print("Visit http://localhost:5000 and try to login")
    print("Check error_output.txt for any errors\n")
    
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
    
except Exception as e:
    sys.stderr.write(f"\n\nFATAL ERROR: {type(e).__name__}: {e}\n\n")
    traceback.print_exc(file=sys.stderr)
    sys.stderr.file.close()
    sys.exit(1)
