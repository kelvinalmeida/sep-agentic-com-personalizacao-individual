
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Fallback config similar to docker-compose if env var is missing
DB_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@control:5432/control_db")

# Try to connect and modify schema
try:
    print(f"Connecting to {DB_URL}...")
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cursor = conn.cursor()

    # Check if column exists
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='session' AND column_name='end_on_next_completion';
    """)
    if not cursor.fetchone():
        print("Adding column 'end_on_next_completion'...")
        cursor.execute("ALTER TABLE session ADD COLUMN end_on_next_completion BOOLEAN DEFAULT FALSE;")
        print("Column added.")
    else:
        print("Column 'end_on_next_completion' already exists.")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_student_state (
            session_id INTEGER NOT NULL,
            student_id VARCHAR(50) NOT NULL,
            current_tactic_index INTEGER NOT NULL DEFAULT 0,
            executed_indices TEXT NOT NULL DEFAULT '[]',
            current_tactic_started_at TIMESTAMP,
            last_rating INTEGER,
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            PRIMARY KEY (session_id, student_id),
            CONSTRAINT fk_session_student_state_session
                FOREIGN KEY (session_id) REFERENCES session(id) ON DELETE CASCADE
        );
    """)
    cursor.execute("""
        ALTER TABLE session_student_state
        ADD COLUMN IF NOT EXISTS current_tactic_started_at TIMESTAMP;
    """)
    print("Ensured table 'session_student_state'.")

    conn.close()

except Exception as e:
    print(f"Error: {e}")
