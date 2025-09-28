#!/usr/bin/env python3
"""
Migration: Add transaction_id column to category_rules table

This migration adds the transaction_id column to support transaction-specific rules
while preserving all existing data.
"""

import sqlite3
import sys
from pathlib import Path

def run_migration():
    """Add transaction_id column to category_rules table."""
    
    # Database path
    db_path = Path(__file__).parent.parent / "data" / "database.sqlite"
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        print("Please ensure the backend has been started at least once to create the database.")
        return False
    
    print(f"Running migration on database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(category_rules)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'transaction_id' in columns:
            print("✅ Column 'transaction_id' already exists. Migration not needed.")
            return True
        
        print("📝 Adding transaction_id column...")
        
        # Add the new column (NULL by default for existing rows)
        cursor.execute("""
            ALTER TABLE category_rules 
            ADD COLUMN transaction_id INTEGER REFERENCES transactions(id) ON DELETE CASCADE
        """)
        
        # Create index on the new column for performance
        print("📝 Creating index on transaction_id...")
        cursor.execute("""
            CREATE INDEX ix_category_rules_transaction_id 
            ON category_rules(transaction_id)
        """)
        
        # Verify the change
        cursor.execute("PRAGMA table_info(category_rules)")
        columns_after = [row[1] for row in cursor.fetchall()]
        
        if 'transaction_id' in columns_after:
            print("✅ Successfully added transaction_id column")
            
            # Show current schema
            cursor.execute("SELECT sql FROM sqlite_master WHERE name='category_rules'")
            schema = cursor.fetchone()[0]
            print(f"📋 Updated table schema:\n{schema}")
            
            conn.commit()
            return True
        else:
            print("❌ Failed to add column")
            return False
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def rollback_migration():
    """Rollback the migration by removing the transaction_id column."""
    print("⚠️  Rolling back migration...")
    
    db_path = Path(__file__).parent.parent / "data" / "database.sqlite"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
        print("📝 Creating backup of category_rules...")
        
        # Get current data
        cursor.execute("SELECT id, text, entity, category_id FROM category_rules")
        existing_data = cursor.fetchall()
        
        # Drop the table and recreate without transaction_id
        cursor.execute("DROP TABLE category_rules")
        
        cursor.execute("""
            CREATE TABLE category_rules (
                id INTEGER PRIMARY KEY,
                text VARCHAR(1000),
                entity VARCHAR(500) NOT NULL,
                category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
                UNIQUE(entity, text)
            )
        """)
        
        cursor.execute("CREATE INDEX ix_category_rules_entity ON category_rules(entity)")
        
        # Restore the data
        cursor.executemany(
            "INSERT INTO category_rules (id, text, entity, category_id) VALUES (?, ?, ?, ?)",
            existing_data
        )
        
        print(f"✅ Rollback completed. Restored {len(existing_data)} category rules.")
        conn.commit()
        
    except sqlite3.Error as e:
        print(f"❌ Rollback failed: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        rollback_migration()
    else:
        success = run_migration()
        if not success:
            sys.exit(1)
        print("\n🚀 Migration completed successfully!")
        print("You can now use transaction-specific category rules.")