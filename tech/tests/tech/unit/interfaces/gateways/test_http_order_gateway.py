import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx
from tech.interfaces.gateways.http_order_gateway import HttpOrderGateway


class TestHttpOrderGateway:
    @pytest.fixture
    def gateway(self):
        return HttpOrderGateway(base_url="http://test-api.com")

    @pytest.mark.asyncio
    async def test_init(self):
        base_url = "http://test-api.com"
        gateway = HttpOrderGateway(base_url=base_url)

        assert gateway.base_url == base_url
        assert gateway.timeout == 10.0

    @pytest.mark.asyncio
    async def test_get_order_success(self, gateway):
        order_id = 123
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"id": order_id, "total_price": 100.0}

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response

        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await gateway.get_order(order_id)

            mock_client.get.assert_awaited_once_with(
                f"http://test-api.com/orders/{order_id}",
                timeout=10.0
            )
            mock_response.raise_for_status.assert_called_once()
            mock_response.json.assert_called_once()

            assert result["id"] == order_id
            assert result["total_price"] == 100.0

    @pytest.mark.asyncio
    async def test_get_order_not_found(self, gateway):
        order_id = 123

        mock_response = Mock()
        http_error = httpx.HTTPStatusError(
            "Not Found",
            request=Mock(),
            response=Mock()
        )
        http_error.response.status_code = 404
        mock_response.raise_for_status.side_effect = http_error

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response

        with patch('httpx.AsyncClient', return_value=mock_client):
            with pytest.raises(ValueError, match=f"Order with ID {order_id} not found"):
                await gateway.get_order(order_id)

            mock_client.get.assert_awaited_once()
            mock_response.raise_for_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_order_http_error(self, gateway):
        order_id = 123

        mock_response = Mock()
        http_error = httpx.HTTPStatusError(
            "Server Error",
            request=Mock(),
            response=Mock()
        )
        http_error.response.status_code = 500
        mock_response.raise_for_status.side_effect = http_error

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response

        with patch('httpx.AsyncClient', return_value=mock_client):
            with pytest.raises(ValueError, match=f"Error fetching order {order_id}"):
                await gateway.get_order(order_id)

            mock_client.get.assert_awaited_once()
            mock_response.raise_for_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_order_request_error(self, gateway):
        order_id = 123

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.side_effect = httpx.RequestError("Connection error", request=Mock())

        with patch('httpx.AsyncClient', return_value=mock_client):
            with pytest.raises(ValueError, match="Failed to communicate with orders service"):
                await gateway.get_order(order_id)

            mock_client.get.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_order_generic_error(self, gateway):
        order_id = 123

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.side_effect = Exception("Generic error")

        with patch('httpx.AsyncClient', return_value=mock_client):
            with pytest.raises(ValueError, match="Failed to communicate with orders service"):
                await gateway.get_order(order_id)

            mock_client.get.assert_awaited_once()