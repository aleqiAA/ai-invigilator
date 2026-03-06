from sqlalchemy import create_engine, text

passwords = ['postgres', 'admin', 'root', 'password', '123456', 'admin123', '']

print("Testing common PostgreSQL passwords...\n")

for pwd in passwords:
    try:
        if pwd == '':
            db_url = 'postgresql://postgres:@localhost:5432/ai_invigilator'
            print(f"Trying: (empty password)")
        else:
            db_url = f'postgresql://postgres:{pwd}@localhost:5432/ai_invigilator'
            print(f"Trying: {pwd}")
        
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"SUCCESS! Password is: {pwd if pwd else '(empty)'}\n")
            print(f"Update your .env file with:")
            print(f"DATABASE_URL={db_url}")
            break
    except Exception as e:
        print(f"Failed: {str(e)[:50]}\n")
else:
    print("\nNone of the common passwords worked.")
    print("You need to reset PostgreSQL password or check if PostgreSQL is running.")
