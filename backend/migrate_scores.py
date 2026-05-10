import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

def migrate():
    try:
        conn = pymysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASS", "root"),
            port=int(os.getenv("DB_PORT", "3306")),
            database=os.getenv("DB_NAME", "interview_echo"),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = conn.cursor()
        
        print("Checking for existing columns in 'evaluations' table...")
        cursor.execute("SHOW COLUMNS FROM evaluations")
        columns = [col['Field'] for col in cursor.fetchall()]
        
        if "business_scenario_score" not in columns:
            print("Adding column 'business_scenario_score'...")
            cursor.execute("ALTER TABLE evaluations ADD COLUMN business_scenario_score FLOAT DEFAULT 0.0")
        else:
            print("Column 'business_scenario_score' already exists.")
            
        if "problem_solving_score" not in columns:
            print("Adding column 'problem_solving_score'...")
            cursor.execute("ALTER TABLE evaluations ADD COLUMN problem_solving_score FLOAT DEFAULT 0.0")
        else:
            print("Column 'problem_solving_score' already exists.")
            
        conn.commit()
        print("Migration completed successfully.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    migrate()
