import winreg
import os

# Check common installation paths
paths = [
    r"C:\Program Files\PostgreSQL\16\bin",
    r"C:\Program Files\PostgreSQL\15\bin",
    r"C:\Program Files\PostgreSQL\14\bin",
    r"C:\Program Files (x86)\PostgreSQL\16\bin",
    r"C:\Program Files (x86)\PostgreSQL\15\bin",
]

print("Checking common PostgreSQL paths:")
for path in paths:
    if os.path.exists(path):
        print(f"FOUND: {path}")
        print(f"\nTo reset password, run as Administrator:")
        print(f'cd "{path}"')
        print(f'psql -U postgres')
    else:
        print(f"Not found: {path}")

# Check Windows Registry
print("\n\nChecking Windows Registry:")
try:
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\PostgreSQL\Installations")
    i = 0
    while True:
        try:
            subkey_name = winreg.EnumKey(key, i)
            subkey = winreg.OpenKey(key, subkey_name)
            base_dir = winreg.QueryValueEx(subkey, "Base Directory")[0]
            print(f"PostgreSQL found: {base_dir}")
            print(f"  Bin directory: {os.path.join(base_dir, 'bin')}")
            winreg.CloseKey(subkey)
            i += 1
        except WindowsError:
            break
    winreg.CloseKey(key)
except:
    print("No PostgreSQL installations found in registry")

# Check services
print("\n\nTo find PostgreSQL service:")
print("1. Press Win+R, type 'services.msc', press Enter")
print("2. Look for 'postgresql' service")
print("3. Right-click -> Properties")
print("4. Check 'Path to executable' field")
