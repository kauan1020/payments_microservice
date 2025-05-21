import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock, create_autospec
import os
import sys
import json
import logging
import asyncio
import pika
import uuid
from datetime import datetime
from tech.domain.entities.payments import Payment, PaymentStatus


class TestRunPaymentRequestWorker:
    @pytest.fixture
    def mock_repository(self):
        return Mock()

    @pytest.fixture
    def mock_broker(self):
        broker = Mock()
        broker.publish_async = AsyncMock()
        return broker

    @pytest.fixture
    def mock_processor(self):
        processor = Mock()
        processor.process = AsyncMock()
        return processor

    @pytest.fixture
    def payment_request(self):
        return {
            "order_id": 123,
            "amount": 100.0,
            "payment_method": "credit_card"
        }

    @pytest.mark.asyncio
    async def test_simple_payment_processor_init(self):
        with patch('tech.workers.run_payment_request_worker.SQLAlchemyPaymentRepository') as mock_repo_class, \
                patch('tech.workers.run_payment_request_worker.MockPaymentProvider') as mock_provider_class, \
                patch('tech.workers.run_payment_request_worker.logger') as mock_logger, \
                patch('inspect.iscoroutinefunction', return_value=True):
            repository = Mock()
            broker = Mock()
            provider = Mock()

            mock_repo_class.return_value = repository
            mock_provider_class.return_value = provider

            from tech.workers.run_payment_request_worker import SimplePaymentProcessor

            processor = SimplePaymentProcessor(repository, broker)

            assert processor.repository == repository
            assert processor.broker == broker
            assert processor.provider == provider
            mock_provider_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_simple_payment_processor_init_sync_method(self):
        with patch('tech.workers.run_payment_request_worker.MockPaymentProvider') as mock_provider_class, \
                patch('tech.workers.run_payment_request_worker.logger') as mock_logger, \
                patch('inspect.iscoroutinefunction', return_value=False), \
                patch('asyncio.iscoroutinefunction') as mock_is_coro:
            mock_is_coro.return_value = True

            repository = Mock()
            broker = Mock()
            provider = Mock()
            provider.process_payment = Mock()

            mock_provider_class.return_value = provider

            from tech.workers.run_payment_request_worker import SimplePaymentProcessor

            processor = SimplePaymentProcessor(repository, broker)

            mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_simple_payment_processor_init_exception(self):
        with patch('tech.workers.run_payment_request_worker.MockPaymentProvider',
                   side_effect=Exception("Error creating provider")), \
                patch('tech.workers.run_payment_request_worker.logger') as mock_logger, \
                patch('asyncio.iscoroutinefunction') as mock_is_coro:
            mock_is_coro.return_value = True

            repository = Mock()
            broker = Mock()

            from tech.workers.run_payment_request_worker import SimplePaymentProcessor

            processor = SimplePaymentProcessor(repository, broker)

            assert hasattr(processor.provider, 'process_payment')
            mock_logger.error.assert_called()


    @pytest.mark.asyncio
    async def test_process_provider_error(self, mock_repository, mock_broker, payment_request):
        mock_provider = AsyncMock()
        mock_provider.process_payment.side_effect = Exception("Provider error")

        with patch('tech.workers.run_payment_request_worker.datetime') as mock_datetime, \
                patch('asyncio.sleep'):
            mock_datetime.now.return_value = datetime.now()

            from tech.workers.run_payment_request_worker import SimplePaymentProcessor

            payment = Payment(
                order_id=123,
                amount=100.0,
                status=PaymentStatus.PROCESSING
            )
            mock_repository.add.return_value = payment

            processor = SimplePaymentProcessor(mock_repository, mock_broker)
            processor.provider = mock_provider
            processor.publish_response = AsyncMock()

            result = await processor.process(payment_request)

            mock_repository.add.assert_called_once()
            mock_provider.process_payment.assert_awaited_once()
            assert payment.status == PaymentStatus.ERROR
            assert payment.error_message == "Provider error"
            mock_repository.update.assert_called_once()
            processor.publish_response.assert_awaited_once()
            assert result == payment

    @pytest.mark.asyncio
    async def test_process_type_error_none_await(self, mock_repository, mock_broker, payment_request):
        mock_provider = AsyncMock()
        mock_provider.process_payment.side_effect = TypeError("object NoneType can't be used in 'await'")

        with patch('tech.workers.run_payment_request_worker.datetime') as mock_datetime, \
                patch('tech.workers.run_payment_request_worker.uuid.uuid4') as mock_uuid, \
                patch('asyncio.sleep'):
            mock_datetime.now.return_value = datetime.now()
            mock_uuid.return_value = Mock(hex="1234567890abcdef")

            from tech.workers.run_payment_request_worker import SimplePaymentProcessor

            payment = Payment(
                order_id=123,
                amount=100.0,
                status=PaymentStatus.PROCESSING
            )
            mock_repository.add.return_value = payment

            processor = SimplePaymentProcessor(mock_repository, mock_broker)
            processor.provider = mock_provider
            processor.publish_response = AsyncMock()

            result = await processor.process(payment_request)

            mock_repository.add.assert_called_once()
            mock_provider.process_payment.assert_awaited_once()
            assert payment.status == PaymentStatus.APPROVED
            assert "emergency_" in payment.transaction_id
            mock_repository.update.assert_called_once()
            processor.publish_response.assert_awaited_once()
            assert result == payment

    @pytest.mark.asyncio
    async def test_publish_response_async(self, mock_repository, mock_broker):
        with patch('tech.workers.run_payment_request_worker.logger'):
            from tech.workers.run_payment_request_worker import SimplePaymentProcessor

            processor = SimplePaymentProcessor(mock_repository, mock_broker)

            await processor.publish_response(
                order_id=123,
                status="APPROVED",
                transaction_id="tx_123"
            )

            mock_broker.publish_async.assert_awaited_once_with(
                queue='payment_responses',
                message={
                    'order_id': 123,
                    'status': "APPROVED",
                    'transaction_id': "tx_123"
                }
            )

    @pytest.mark.asyncio
    async def test_publish_response_error(self, mock_repository, mock_broker):
        mock_broker.publish_async.side_effect = Exception("Broker error")

        with patch('tech.workers.run_payment_request_worker.logger') as mock_logger:
            from tech.workers.run_payment_request_worker import SimplePaymentProcessor

            processor = SimplePaymentProcessor(mock_repository, mock_broker)

            await processor.publish_response(
                order_id=123,
                status="ERROR",
                error="Test error"
            )

            mock_broker.publish_async.assert_awaited_once()
            mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_process_message(self, payment_request, mock_processor):
        session_mock = Mock()
        session_gen_mock = Mock()
        session_gen_mock.__next__ = Mock(return_value=session_mock)

        with patch('tech.workers.run_payment_request_worker.get_session', return_value=session_gen_mock), \
                patch('tech.workers.run_payment_request_worker.SQLAlchemyPaymentRepository') as mock_repo_class, \
                patch('tech.workers.run_payment_request_worker.create_async_rabbitmq_broker') as mock_broker_fn, \
                patch('tech.workers.run_payment_request_worker.SimplePaymentProcessor') as mock_processor_class, \
                patch('tech.workers.run_payment_request_worker.logger'):
            repository_mock = Mock()
            broker_mock = Mock()

            mock_repo_class.return_value = repository_mock
            mock_broker_fn.return_value = broker_mock
            mock_processor_class.return_value = mock_processor

            from tech.workers.run_payment_request_worker import process_message

            await process_message(payment_request)

            session_gen_mock.__next__.assert_called_once()
            mock_repo_class.assert_called_once_with(session_mock)
            mock_broker_fn.assert_called_once()
            mock_processor_class.assert_called_once_with(repository_mock, broker_mock)

            mock_processor.process.assert_awaited_once_with(payment_request)
            session_mock.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_exception(self, payment_request):
        session_mock = Mock()
        session_gen_mock = Mock()
        session_gen_mock.__next__ = Mock(return_value=session_mock)

        with patch('tech.workers.run_payment_request_worker.get_session', return_value=session_gen_mock), \
                patch('tech.workers.run_payment_request_worker.SQLAlchemyPaymentRepository',
                      side_effect=Exception("Repo error")), \
                patch('tech.workers.run_payment_request_worker.logger') as mock_logger:
            from tech.workers.run_payment_request_worker import process_message

            await process_message(payment_request)

            session_gen_mock.__next__.assert_called_once()
            mock_logger.error.assert_called()
            session_mock.close.assert_called_once()


    def test_callback_json_error(self):
        ch = Mock()
        method = Mock()
        method.delivery_tag = "tag123"
        properties = Mock()
        body = b"invalid json"

        with patch('tech.workers.run_payment_request_worker.logger') as mock_logger:
            from tech.workers.run_payment_request_worker import callback

            callback(ch, method, properties, body)

            mock_logger.error.assert_called()
            ch.basic_ack.assert_called_once_with(delivery_tag="tag123")

    def test_callback_exception(self, payment_request):
        ch = Mock()
        method = Mock()
        method.delivery_tag = "tag123"
        properties = Mock()
        body = json.dumps(payment_request).encode()

        with patch('tech.workers.run_payment_request_worker.asyncio.run',
                   side_effect=Exception("Process error")), \
                patch('tech.workers.run_payment_request_worker.logger') as mock_logger:
            from tech.workers.run_payment_request_worker import callback

            callback(ch, method, properties, body)

            mock_logger.error.assert_called()
            ch.basic_nack.assert_called_once_with(delivery_tag="tag123", requeue=True)

    def test_main(self):
        connection_mock = Mock()
        channel_mock = Mock()
        connection_mock.channel.return_value = channel_mock

        with patch('tech.workers.run_payment_request_worker.pika.PlainCredentials') as mock_creds, \
                patch('tech.workers.run_payment_request_worker.pika.ConnectionParameters') as mock_params, \
                patch('tech.workers.run_payment_request_worker.pika.BlockingConnection',
                      return_value=connection_mock), \
                patch('tech.workers.run_payment_request_worker.logger'), \
                patch('sys.exit') as mock_exit:
            mock_creds.return_value = "fake_creds"
            mock_params.return_value = "fake_params"

            channel_mock.start_consuming.side_effect = KeyboardInterrupt()

            from tech.workers.run_payment_request_worker import main

            main()

            mock_creds.assert_called_once()
            mock_params.assert_called_once()
            connection_mock.channel.assert_called_once()
            channel_mock.queue_declare.assert_called()
            channel_mock.basic_qos.assert_called_once_with(prefetch_count=1)
            channel_mock.basic_consume.assert_called_once()
            channel_mock.start_consuming.assert_called_once()

            mock_exit.assert_called_once_with(0)

    def test_main_exception(self):
        with patch('tech.workers.run_payment_request_worker.pika.PlainCredentials',
                   side_effect=Exception("Connection error")), \
                patch('tech.workers.run_payment_request_worker.logger') as mock_logger, \
                patch('sys.exit') as mock_exit:
            from tech.workers.run_payment_request_worker import main

            main()

            mock_logger.error.assert_called()
            mock_exit.assert_called_once_with(1)

    def test_wrap_sync_method(self):
        with patch('tech.workers.run_payment_request_worker.logger'):
            from tech.workers.run_payment_request_worker import SimplePaymentProcessor

            repository = Mock()
            broker = Mock()
            processor = SimplePaymentProcessor(repository, broker)

            original_method = Mock(return_value="test_result")
            processor.provider.process_payment = original_method

            processor._wrap_sync_method()

            assert asyncio.iscoroutinefunction(processor.provider.process_payment)

    def test_create_emergency_provider(self):
        with patch('tech.workers.run_payment_request_worker.logger'):
            from tech.workers.run_payment_request_worker import SimplePaymentProcessor

            repository = Mock()
            broker = Mock()
            processor = SimplePaymentProcessor(repository, broker)

            processor._create_emergency_provider()

            assert hasattr(processor.provider, 'process_payment')
            assert asyncio.iscoroutinefunction(processor.provider.process_payment)