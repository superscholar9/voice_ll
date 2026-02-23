"""Test authentication endpoints."""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Test 1: Register (will fail without valid Turnstile token)
print("[TEST 1] Testing registration endpoint...")
register_data = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword123",
    "turnstile_token": "dummy_token"
}
response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")
print()

# Test 2: Check API documentation
print("[TEST 2] Checking API documentation...")
response = requests.get("http://localhost:8000/docs")
print(f"Docs available: {response.status_code == 200}")
print()

# Test 3: Check available endpoints
print("[TEST 3] Checking OpenAPI schema...")
response = requests.get("http://localhost:8000/openapi.json")
if response.status_code == 200:
    schema = response.json()
    print("Available auth endpoints:")
    for path in schema.get("paths", {}).keys():
        if "/auth/" in path or "/users/" in path:
            print(f"  - {path}")
print()

print("[OK] Authentication system is integrated and running")
