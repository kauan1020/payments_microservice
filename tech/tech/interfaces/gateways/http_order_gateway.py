# tech/interfaces/gateways/http_order_gateway.py
import httpx
from typing import Dict, Any, Optional


class HttpOrderGateway:
    """
    Gateway for HTTP communication with the orders service.

    This gateway encapsulates the details of HTTP communication with the orders service,
    allowing use cases to access order data without being coupled to HTTP implementation.
    """

    def __init__(self, base_url: str):
        """
        Initialize the gateway with the base URL of the orders service.

        Args:
            base_url: Base URL of the orders service API.
        """
        self.base_url = base_url
        self.timeout = 10.0  # Timeout in seconds

    async def get_order(self, order_id: int) -> Dict[str, Any]:
        """
        Retrieve order details by ID from the orders service.

        Args:
            order_id: The unique identifier of the order.

        Returns:
            A dictionary containing order details.

        Raises:
            ValueError: If the order is not found or communication fails.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/orders/{order_id}",
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise ValueError(f"Order with ID {order_id} not found")
                else:
                    raise ValueError(f"Error fetching order {order_id}: {str(e)}")
            except (httpx.RequestError, Exception) as e:
                raise ValueError(f"Failed to communicate with orders service: {str(e)}")