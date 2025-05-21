import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from tech.infra.rabbitmq_broker import RabbitMQBroker
from tech.infra.async_rabbitmq_broker import AsyncRabbitMQBroker, create_async_rabbitmq_broker


class TestAsyncRabbitMQBroker:
    @pytest.fixture
    def sync_broker_mock(self):
        mock = Mock(spec=RabbitMQBroker)
        return mock

    @pytest.fixture
    def broker(self, sync_broker_mock):
        with patch('tech.infra.async_rabbitmq_broker.RabbitMQBroker', return_value=sync_broker_mock):
            broker = AsyncRabbitMQBroker(
                host="localhost",
                port=5672,
                user="guest",
                password="password"
            )
            return broker

    def test_init(self, sync_broker_mock):
        with patch('tech.infra.async_rabbitmq_broker.RabbitMQBroker', return_value=sync_broker_mock) as mock_rabbit:
            broker = AsyncRabbitMQBroker(
                host="test_host",
                port=1234,
                user="test_user",
                password="test_password"
            )

            mock_rabbit.assert_called_once_with(
                host="test_host",
                port=1234,
                user="test_user",
                password="test_password"
            )
            assert broker.sync_broker == sync_broker_mock

    def test_publish(self, broker, sync_broker_mock):
        queue = "test_queue"
        message = {"key": "value"}

        broker.publish(queue, message)

        sync_broker_mock.publish.assert_called_once_with(queue, message)

    @pytest.mark.asyncio
    async def test_publish_async(self, broker, sync_broker_mock):
        queue = "test_queue"
        message = {"key": "value"}

        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = AsyncMock()
            mock_get_loop.return_value = mock_loop

            await broker.publish_async(queue, message)

            mock_get_loop.assert_called_once()
            mock_loop.run_in_executor.assert_called_once()

            lambda_func = mock_loop.run_in_executor.call_args[0][1]
            lambda_func()
            sync_broker_mock.publish.assert_called_once_with(queue, message)

    def test_consume(self, broker, sync_broker_mock):
        queue = "test_queue"
        callback = lambda x: None

        broker.consume(queue, callback)

        sync_broker_mock.consume.assert_called_once_with(queue, callback)

    def test_close(self, broker, sync_broker_mock):
        broker.close()

        sync_broker_mock.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_async(self, broker, sync_broker_mock):
        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = AsyncMock()
            mock_get_loop.return_value = mock_loop

            await broker.close_async()

            mock_get_loop.assert_called_once()
            mock_loop.run_in_executor.assert_called_once()

            lambda_func = mock_loop.run_in_executor.call_args[0][1]
            lambda_func()
            sync_broker_mock.close.assert_called_once()

    def test_create_async_rabbitmq_broker(self, sync_broker_mock):
        with patch('tech.infra.async_rabbitmq_broker.AsyncRabbitMQBroker') as mock_async_rabbit:
            broker = create_async_rabbitmq_broker(
                host="test_host",
                port=1234,
                user="test_user",
                password="test_password"
            )

            mock_async_rabbit.assert_called_once_with(
                host="test_host",
                port=1234,
                user="test_user",
                password="test_password"
            )
            assert broker == mock_async_rabbit.return_value