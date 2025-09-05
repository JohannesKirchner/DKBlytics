# frontend/api/client.py
import httpx

BASE_URL = "http://127.0.0.1:8000"  # Adjust if your FastAPI runs elsewhere

class APIClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url)

    def get(self, endpoint: str, params: dict = None):
        response = self.client.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, data: dict):
        response = self.client.post(endpoint, json=data)
        response.raise_for_status()
        return response.json()

    def delete(self, endpoint: str):
        response = self.client.delete(endpoint)
        response.raise_for_status()
        return response.status_code
