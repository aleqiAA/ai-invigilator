import sys
from sqlalchemy import create_engine, text

print("PostgreSQL Database Creation Script")
print("=" * 50)

password = input("Enter your PostgreSQL 'postgres' user password: ")

try:
    # Connect to default postgres database
    engine = create_engine(f'postgresql://postgres:{password}@localhost:5432/postgres')
    
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        
        # Check if database exists
        result = conn.execute(text("SELECT 1 FROM pg_database WHERE datname='ai_invigilator'"))
        exists = result.fetchone()
        
        if exists:
            print("\nDatabase 'ai_invigilator' already exists!")
        else:
            conn.execute(text("CREATE DATABASE ai_invigilator"))
            print("\nDatabase 'ai_invigilator' created successfully!")
        
        print(f"\nYour DATABASE_URL is:")
        print(f"postgresql://postgres:{password}@localhost:5432/ai_invigilator")
        print("\nCopy this to your .env file")
        
except Exception as e:
    print(f"\nError: {e}")
    print("\nMake sure:")
    print("1. PostgreSQL is installed")
    print("2. PostgreSQL service is running")
    print("3. Password is correct")
    sys.exit(1)
