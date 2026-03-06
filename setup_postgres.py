from sqlalchemy import create_engine, text

# Winget PostgreSQL often uses these defaults
passwords = ['postgres', 'root', 'admin', '']

print("Testing PostgreSQL connection...")

for pwd in passwords:
    try:
        db_url = f'postgresql://postgres:{pwd}@localhost:5432/postgres'
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT")
            
            print(f"\nCONNECTED! Password is: '{pwd}' (empty string if blank)")
            
            # Check if database exists
            result = conn.execute(text("SELECT 1 FROM pg_database WHERE datname='ai_invigilator'"))
            exists = result.fetchone()
            
            if exists:
                print("Database 'ai_invigilator' already exists")
            else:
                conn.execute(text("CREATE DATABASE ai_invigilator"))
                print("Database 'ai_invigilator' created!")
            
            final_url = f'postgresql://postgres:{pwd}@localhost:5432/ai_invigilator'
            print(f"\nYour DATABASE_URL:")
            print(final_url)
            
            # Write to file for easy copy
            with open('database_url.txt', 'w') as f:
                f.write(final_url)
            print("\nSaved to: database_url.txt")
            break
            
    except Exception as e:
        print(f"Password '{pwd}': Failed")
        continue
else:
    print("\n\nNo default password worked.")
    print("Winget installation may require manual password setup.")
    print("Check: C:\\Program Files\\PostgreSQL\\16\\data\\pg_hba.conf")
