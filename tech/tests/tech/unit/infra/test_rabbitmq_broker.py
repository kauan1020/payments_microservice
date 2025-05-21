import pytest
from unittest.mock import Mock, patch, call, MagicMock
import pika
from tech.infra.rabbitmq_broker import RabbitMQBroker


class TestRabbitMQBroker:
    @pytest.fixture
    def connection_mock(self):
        connection = Mock(spec=pika.BlockingConnection)
        return connection

    @pytest.fixture
    def channel_mock(self):
        channel = Mock()
        return channel

    @pytest.fixture
    def broker(self, connection_mock, channel_mock):
        connection_mock.channel.return_value = channel_mock
        with patch('pika.ConnectionParameters') as mock_params, \
                patch('pika.PlainCredentials') as mock_credentials, \
                patch('pika.BlockingConnection', return_value=connection_mock):
            mock_credentials.return_value = "fake_credentials"
            mock_params.return_value = "fake_params"

            broker = RabbitMQBroker(
                host="localhost",
                port=5672,
                user="guest",
                password="password"
            )
            return broker

    def test_init(self, connection_mock, channel_mock):
        with patch('pika.ConnectionParameters') as mock_params, \
                patch('pika.PlainCredentials') as mock_credentials, \
                patch('pika.BlockingConnection', return_value=connection_mock) as mock_connection:
            mock_credentials.return_value = "fake_credentials"
            mock_params.return_value = "fake_params"

            broker = RabbitMQBroker(
                host="test_host",
                port=1234,
                user="test_user",
                password="test_password"
            )

            mock_credentials.assert_called_once_with("test_user", "test_password")
            mock_params.assert_called_once_with(
                host="test_host",
                port=1234,
                credentials="fake_credentials",
                heartbeat=600,
                blocked_connection_timeout=300
            )
            mock_connection.assert_called_once_with("fake_params")
            connection_mock.channel.assert_called_once()
            assert broker.connection == connection_mock
            # Corrigido: devemos verificar se o canal é o retorno do channel()
            assert broker.channel == connection_mock.channel.return_value

    def test_publish(self, broker, channel_mock):
        queue = "test_queue"
        message = {"key": "value"}

        broker.publish(queue, message)

        channel_mock.queue_declare.assert_called_once_with(queue=queue, durable=True)
        channel_mock.basic_publish.assert_called_once()

        publish_call = channel_mock.basic_publish.call_args
        assert publish_call.kwargs['exchange'] == ''
        assert publish_call.kwargs['routing_key'] == queue
        assert 'body' in publish_call.kwargs
        assert 'properties' in publish_call.kwargs

    def test_consume(self, broker, channel_mock):
        queue = "test_queue"
        callback = Mock()

        broker.consume(queue, callback)

        channel_mock.queue_declare.assert_called_once_with(queue=queue, durable=True)
        channel_mock.basic_qos.assert_called_once_with(prefetch_count=1)
        channel_mock.basic_consume.assert_called_once()
        channel_mock.start_consuming.assert_called_once()

        consume_call = channel_mock.basic_consume.call_args
        assert consume_call.kwargs['queue'] == queue

        wrapped_callback = consume_call.kwargs['on_message_callback']

        ch = Mock()
        method = Mock()
        method.delivery_tag = "tag1"
        properties = Mock()
        body = '{"data": "test"}'.encode()

        wrapped_callback(ch, method, properties, body)

        callback.assert_called_once_with({"data": "test"})
        ch.basic_ack.assert_called_once_with(delivery_tag="tag1")

    def test_close(self, broker, connection_mock):
        connection_mock.is_open = True

        broker.close()

        connection_mock.close.assert_called_once()

    def test_close_not_open(self, broker, connection_mock):
        connection_mock.is_open = False

        broker.close()

        connection_mock.close.assert_not_called()