import sys
import django
import sqlite3
from django.conf import settings

print("=" * 50)
print("DJANGO & SQLITE HEALTH CHECK")
print("=" * 50)

# 1. Check Python version
print(f"1. Python Version: {sys.version}")

# 2. Check Django version
print(f"2. Django Version: {django.__version__}")

# 3. Check SQLite version
print(f"3. SQLite Version: {sqlite3.sqlite_version}")

# 4. Check Django settings
try:
    settings.configure() if not settings.configured else None
    print("4. Django Settings: ✓ OK")
except Exception as e:
    print(f"4. Django Settings: ✗ ERROR - {e}")

# 5. Test SQLite database creation
try:
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT);")
    cursor.execute("INSERT INTO test (name) VALUES ('test_record');")
    cursor.execute("SELECT * FROM test;")
    result = cursor.fetchone()
    conn.close()
    print("5. SQLite Operations: ✓ OK (Created table, inserted, queried)")
except Exception as e:
    print(f"5. SQLite Operations: ✗ ERROR - {e}")

print("=" * 50)
print("HEALTH CHECK COMPLETE")
print("=" * 50)
