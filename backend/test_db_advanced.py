import os
import socket
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"DATABASE_URL: {DATABASE_URL}\n")

# Extract hostname
hostname = "db.anijoaymwjzwrkxnpzwd.supabase.co"

print(f"Testing hostname: {hostname}")
try:
    ip = socket.gethostbyname(hostname)
    print(f"✅ DNS resolved: {hostname} → {ip}")
except socket.gaierror as e:
    print(f"❌ DNS resolution failed: {e}")
    print("\nTrying alternatives...")

    # Try with socket.getaddrinfo
    try:
        result = socket.getaddrinfo(hostname, 5432)
        print(f"✅ getaddrinfo worked: {result}")
    except Exception as e2:
        print(f"❌ getaddrinfo also failed: {e2}")

print("\n" + "="*50)
print("Now trying database connection...")
print("="*50 + "\n")

try:
    import psycopg2
    # Try with sslmode=require
    conn = psycopg2.connect(DATABASE_URL + "?sslmode=require")
    print("✅ Connection successful!")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
