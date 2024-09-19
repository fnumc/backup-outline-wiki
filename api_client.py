import requests
from typing import Any

class APIError(Exception):
    pass

class OutlineAPIClient:
    def __init__(self, host: str, token: str):
        self.host = host
        self.headers = {
            'Content-Type': "application/json",
            'Authorization': f"Bearer {token}"
        }

    def _make_request(self, method: str, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"https://{self.host}{endpoint}"
        response = requests.request(method, url, json=data, headers=self.headers)

        if response.status_code != 200:
            raise APIError(f"Request failed. Status code: {response.status_code}, Response: {response.text}")

        return response.json()

    def request_export(self, format: str = "outline-markdown") -> dict[str, Any]:
        return self._make_request("POST", "/api/collections.export_all", {"format": format})

    def check_export_status(self, file_operation_id: str) -> dict[str, Any]:
        return self._make_request("POST", "/api/fileOperations.info", {"id": file_operation_id})

    def download_file(self, file_operation_id: str) -> bytes:
        redirect_response = requests.get(
            f"https://{self.host}/api/fileOperations.redirect",
            params={"id": file_operation_id},
            headers=self.headers,
            allow_redirects=False
        )

        if redirect_response.status_code != 302:
            raise APIError(f"Expected 302 redirect, got {redirect_response.status_code}. Response: {redirect_response.text}")

        download_url = redirect_response.headers.get('Location')
        if not download_url:
            raise APIError("Redirect location not found in headers")

        file_response = requests.get(download_url, headers=self.headers)

        if file_response.status_code != 200:
            raise APIError(f"File download failed. Status code: {file_response.status_code}, Response: {file_response.text}")

        return file_response.content
