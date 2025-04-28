"""HTTP client module."""
from typing import Any, Dict, Optional

import requests


class HttpClient:
    """Base HTTP client for API interactions.
    
    This client provides a foundation for making HTTP requests to external APIs
    with proper error handling and request configuration.
    """

    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None) -> None:
        """Initialize the HTTP client with a base URL and optional headers.
        
        Args:
            base_url: The base URL for all requests
            headers: Optional headers to include with all requests
        """
        self.base_url = base_url
        # Add a User-Agent header
        default_headers = {
            "User-Agent": "FlowMetrics/1.0 (brett.plemons@gmail.com)" 
        }
        # Merge with any provided headers
        self.headers = headers if headers is not None else default_headers

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ) -> requests.Response:
        """Make an HTTP request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path to append to base_url
            params: Optional query parameters
            json: Optional JSON body
            timeout: Request timeout in seconds
            
        Returns:
            Response object
            
        Raises:
            requests.HTTPError: For 4xx and 5xx responses
        """
        url = f"{self.base_url}{path}"
        response = requests.request(
            method,
            url,
            headers=self.headers,
            params=params,
            json=json,
            timeout=timeout,
        )
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response

    def get(
        self, path: str, params: Optional[Dict[str, Any]] = None, timeout: int = 30
    ) -> requests.Response:
        """Make a GET request.
        
        Args:
            path: URL path to append to base_url
            params: Optional query parameters
            timeout: Request timeout in seconds
            
        Returns:
            Response object
        """
        return self._request("GET", path, params=params, timeout=timeout)

    def post(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ) -> requests.Response:
        """Make a POST request.
        
        Args:
            path: URL path to append to base_url
            params: Optional query parameters
            json: Optional JSON body
            timeout: Request timeout in seconds
            
        Returns:
            Response object
        """
        return self._request("POST", path, params=params, json=json, timeout=timeout)

    def patch(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ) -> requests.Response:
        """Make a PATCH request.
        
        Args:
            path: URL path to append to base_url
            params: Optional query parameters
            json: Optional JSON body
            timeout: Request timeout in seconds
            
        Returns:
            Response object
        """
        return self._request("PATCH", path, params=params, json=json, timeout=timeout)

    def options(
        self, path: str, params: Optional[Dict[str, Any]] = None, timeout: int = 30
    ) -> requests.Response:
        """Make an OPTIONS request.
        
        Args:
            path: URL path to append to base_url
            params: Optional query parameters
            timeout: Request timeout in seconds
            
        Returns:
            Response object
        """
        return self._request("OPTIONS", path, params=params, timeout=timeout)

    def delete(
        self, path: str, params: Optional[Dict[str, Any]] = None, timeout: int = 30
    ) -> requests.Response:
        """Make a DELETE request.
        
        Args:
            path: URL path to append to base_url
            params: Optional query parameters
            timeout: Request timeout in seconds
            
        Returns:
            Response object
        """
        return self._request("DELETE", path, params=params, timeout=timeout)


class HeaderAdder:
    """Utility class for adding headers to an HTTP client."""

    def __init__(self, client: HttpClient, headers: Dict[str, str]) -> None:
        """Initialize the HeaderAdder with a client and headers.
        
        Args:
            client: The HttpClient to modify
            headers: Headers to add to the client
        """
        self.client = client
        self.headers = headers

    def add_headers(self) -> None:
        """Add the headers to the client."""
        self.client.headers.update(self.headers)