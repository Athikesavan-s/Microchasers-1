import requests
import os
from bs4 import BeautifulSoup

# Base URL of the running application
BASE_URL = "http://127.0.0.1:5000"

# Test user credentials
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpassword"
TEST_EMAIL = "test@example.com"

def get_csrf_token(session, url):
    """Fetches the CSRF token from a form."""
    try:
        response = session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        token = soup.find('input', {'name': 'csrf_token'})
        if token:
            return token['value']
        else:
            print(f"CSRF token not found on {url}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching CSRF token from {url}: {e}")
        return None

def main():
    with requests.Session() as session:
        # 1. Register a new user
        register_url = f"{BASE_URL}/auth/register"
        csrf_token = get_csrf_token(session, register_url)
        if not csrf_token:
            return

        register_data = {
            "username": TEST_USERNAME,
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "password2": TEST_PASSWORD,
            "csrf_token": csrf_token,
            "submit": "Register"
        }
        try:
            r = session.post(register_url, data=register_data, allow_redirects=True)
            r.raise_for_status()
            print("Registration successful or user already exists.")
        except requests.exceptions.RequestException as e:
            print(f"Registration failed: {e}")
            return


        # 2. Login
        login_url = f"{BASE_URL}/auth/login"
        csrf_token = get_csrf_token(session, login_url)
        if not csrf_token:
             return

        login_data = {
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
            "csrf_token": csrf_token,
            "submit": "Sign In"
        }
        try:
            r = session.post(login_url, data=login_data, allow_redirects=True)
            r.raise_for_status()
            if "Invalid username or password" in r.text:
                print("Login failed: Invalid username or password")
                return
            print("Login successful.")
        except requests.exceptions.RequestException as e:
            print(f"Login failed: {e}")
            return

        # 3. Create a new sample
        create_sample_url = f"{BASE_URL}/create_sample"
        csrf_token = get_csrf_token(session, create_sample_url)
        if not csrf_token:
            return

        sample_data = {
            "name": "Test Sample",
            "csrf_token": csrf_token,
            "submit": "Create"
        }
        try:
            r = session.post(create_sample_url, data=sample_data, allow_redirects=True)
            r.raise_for_status()
            print("Sample created successfully.")
        except requests.exceptions.RequestException as e:
            print(f"Sample creation failed: {e}")
            return

        # The sample ID is in the URL of the redirect. Let's assume it's the latest one.
        # A better way would be to parse the response and find the link.
        # For this test, let's assume the sample id is 1.
        sample_id = 1


        # 4. Upload an image to the sample
        upload_url = f"{BASE_URL}/sample/{sample_id}"
        csrf_token = get_csrf_token(session, upload_url)
        if not csrf_token:
            return

        image_path = 'test_image.png'
        if not os.path.exists(image_path):
            print(f"Test image not found at {image_path}")
            return

        with open(image_path, 'rb') as f:
            files = {'image': (image_path, f, 'image/png')}
            upload_data = {
                "csrf_token": csrf_token,
                "submit": "Upload"
            }
            try:
                r = session.post(upload_url, files=files, data=upload_data, allow_redirects=True)
                r.raise_for_status()
                print("Image uploaded successfully.")
            except requests.exceptions.RequestException as e:
                print(f"Image upload failed: {e}")
                return

        # 5. Get the dashboard page for the new image
        # We need to find the image_id. We can parse the sample page to find the link to the dashboard.
        try:
            r = session.get(upload_url)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')
            dashboard_link = soup.find('a', text='View Dashboard')
            if dashboard_link:
                dashboard_url = f"{BASE_URL}{dashboard_link['href']}"
                print(f"Found dashboard link: {dashboard_url}")
                r_dashboard = session.get(dashboard_url)
                r_dashboard.raise_for_status()
                if "Analysis Dashboard" in r_dashboard.text:
                    print("Dashboard page loaded successfully!")
                else:
                    print("Dashboard page did not load correctly.")
            else:
                print("Could not find the dashboard link on the sample page.")
        except requests.exceptions.RequestException as e:
            print(f"Failed to get dashboard page: {e}")


if __name__ == "__main__":
    main()
