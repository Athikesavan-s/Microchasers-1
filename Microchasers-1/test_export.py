import requests
import uuid
import os
import json
import csv
import io

# URLs
base_url = 'http://127.0.0.1:5000'
register_url = f'{base_url}/auth/register'
login_url = f'{base_url}/auth/login'
index_url = f'{base_url}/index'
create_sample_url = f'{base_url}/create_sample'

def get_csrf_token(session, url):
    """Gets a CSRF token from a form on a given page."""
    try:
        response = session.get(url)
        response.raise_for_status()
        # Simple string search is brittle but fine for this test script
        start = response.text.find('name="csrf_token" type="hidden" value="') + len('name="csrf_token" type="hidden" value="')
        end = response.text.find('"', start)
        return response.text[start:end]
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error getting CSRF token from {url}: {e}")
        return None

def register_and_login(session):
    """Registers a new user and logs them in."""
    unique_id = str(uuid.uuid4())[:8]
    username = f'export_user_{unique_id}'
    email = f'export_{unique_id}@example.com'
    password = 'password'

    reg_csrf = get_csrf_token(session, register_url)
    reg_data = {'csrf_token': reg_csrf, 'username': username, 'email': email, 'password': password, 'password2': password}
    session.post(register_url, data=reg_data)

    login_csrf = get_csrf_token(session, login_url)
    login_data = {'csrf_token': login_csrf, 'username': username, 'password': password}
    response_login = session.post(login_url, data=login_data)

    if response_login.url == index_url:
        print(f"Successfully logged in as {username}")
        return True
    return False

def create_sample_with_image(session):
    """Creates a sample, uploads an image, and returns the sample ID."""
    # Create sample
    sample_name = f"SampleForExportTest_{str(uuid.uuid4())[:4]}"
    create_csrf = get_csrf_token(session, create_sample_url)
    create_data = {'csrf_token': create_csrf, 'name': sample_name}
    response_create = session.post(create_sample_url, data=create_data)

    # Get sample ID
    response_index = session.get(index_url)
    start_href = response_index.text.find(f'">{sample_name}</a>') - 20 # Look backwards for href
    start_id = response_index.text.find('/sample/', start_href) + len('/sample/')
    end_id = response_index.text.find('"', start_id)
    sample_id = response_index.text[start_id:end_id]
    print(f"Created sample '{sample_name}' with ID {sample_id}")

    # Upload image
    sample_url = f"{base_url}/sample/{sample_id}"
    upload_csrf = get_csrf_token(session, sample_url)
    image_path = 'test_image.png' # Assumes generate_test_image.py was run
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Test image not found at {image_path}. Please generate it first.")

    with open(image_path, 'rb') as f:
        files = {'image': (image_path, f, 'image/png')}
        upload_data = {'csrf_token': upload_csrf, 'submit': 'Upload'}
        session.post(sample_url, data=upload_data, files=files)
    print("Image uploaded to sample.")
    return sample_id


def test_export_feature():
    session = requests.Session()
    if not register_and_login(session):
        return

    sample_id = create_sample_with_image(session)
    if not sample_id:
        return

    # --- 1. Test JSON Export ---
    print("\n--- Testing JSON Export ---")
    json_export_url = f"{base_url}/api/sample/{sample_id}/export/json"
    response_json = session.get(json_export_url)

    if response_json.status_code != 200:
        print(f"JSON export failed with status code {response_json.status_code}")
        return

    try:
        data = response_json.json()
        assert data['id'] == int(sample_id)
        assert 'images' in data
        assert len(data['images']) == 1
        assert 'detections' in data['images'][0]
        # The number of detections can vary, so just check that it's a list
        assert isinstance(data['images'][0]['detections'], list)
        print("JSON export verified successfully.")
    except (json.JSONDecodeError, AssertionError) as e:
        print(f"JSON data validation failed: {e}")
        return

    # --- 2. Test CSV Export ---
    print("\n--- Testing CSV Export ---")
    csv_export_url = f"{base_url}/api/sample/{sample_id}/export/csv"
    response_csv = session.get(csv_export_url)

    if response_csv.status_code != 200:
        print(f"CSV export failed with status code {response_csv.status_code}")
        return

    try:
        # The response content is bytes, decode it to string
        csv_content = response_csv.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_content))
        header = next(csv_reader)
        assert header == ['image_id', 'detection_id', 'x_coordinate', 'y_coordinate', 'confidence']
        first_row = next(csv_reader)
        assert len(first_row) == 5
        print("CSV export verified successfully.")
    except (StopIteration, AssertionError) as e:
        print(f"CSV data validation failed: {e}")
        return

    print("\nData export test completed successfully!")


if __name__ == "__main__":
    # We need the test image for this script
    if not os.path.exists('test_image.png'):
        print("Generating test image...")
        import numpy as np
        import cv2
        image = np.zeros((100, 100, 3), np.uint8)
        cv2.circle(image, (50, 50), 10, (255, 255, 255), -1)
        cv2.imwrite("test_image.png", image)

    test_export_feature()
