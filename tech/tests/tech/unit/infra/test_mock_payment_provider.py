import pytest
import asyncio
import uuid
import random
from unittest.mock import patch
from tech.infra.mock_payment_provider import MockPaymentProvider


class TestMockPaymentProvider:
    @pytest.fixture
    def provider(self):
        return MockPaymentProvider()

    @pytest.mark.asyncio
    async def test_process_payment(self, provider):
        with patch('asyncio.sleep') as mock_sleep:
            mock_sleep.return_value = None

            order_id = 123
            amount = 100.50
            payment_method = "credit_card"

            with patch('uuid.uuid4') as mock_uuid:
                mock_uuid.return_value = uuid.UUID('12345678123456781234567812345678')

                result = await provider.process_payment(order_id, amount, payment_method)

                mock_sleep.assert_called_once_with(0.5)
                assert result["transaction_id"] == "mock_1234567812345678"
                assert result["status"] == "APPROVED"
                assert result["amount"] == amount
                assert result["currency"] == "BRL"
                assert result["order_id"] == order_id
                assert result["payment_method"] == payment_method

    @pytest.mark.asyncio
    async def test_refund_payment_full_amount(self, provider):
        with patch('asyncio.sleep') as mock_sleep, \
                patch('uuid.uuid4') as mock_uuid, \
                patch('random.random') as mock_random:
            mock_sleep.return_value = None
            mock_uuid.return_value = uuid.UUID('12345678123456781234567812345678')
            mock_random.return_value = 0.5  # Should result in success (> 0.1)

            transaction_id = "mock_transaction_123"

            result = await provider.refund_payment(transaction_id)

            mock_sleep.assert_called_once_with(0.5)
            assert result["refund_id"] == "refund_1234567812345678"
            assert result["transaction_id"] == transaction_id
            assert result["status"] == "succeeded"
            assert result["currency"] == "BRL"

    @pytest.mark.asyncio
    async def test_refund_payment_partial_amount(self, provider):
        with patch('asyncio.sleep') as mock_sleep, \
                patch('uuid.uuid4') as mock_uuid, \
                patch('random.random') as mock_random:
            mock_sleep.return_value = None
            mock_uuid.return_value = uuid.UUID('12345678123456781234567812345678')
            mock_random.return_value = 0.5  # Should result in success (> 0.1)

            transaction_id = "mock_transaction_123"
            amount = 50.25

            result = await provider.refund_payment(transaction_id, amount)

            mock_sleep.assert_called_once_with(0.5)
            assert result["refund_id"] == "refund_1234567812345678"
            assert result["transaction_id"] == transaction_id
            assert result["status"] == "succeeded"
            assert result["amount"] == amount
            assert result["currency"] == "BRL"

    @pytest.mark.asyncio
    async def test_refund_payment_failed(self, provider):
        with patch('asyncio.sleep') as mock_sleep, \
                patch('uuid.uuid4') as mock_uuid, \
                patch('random.random') as mock_random:
            mock_sleep.return_value = None
            mock_uuid.return_value = uuid.UUID('12345678123456781234567812345678')
            mock_random.return_value = 0.05  # Should result in failure (< 0.1)

            transaction_id = "mock_transaction_123"

            result = await provider.refund_payment(transaction_id)

            mock_sleep.assert_called_once_with(0.5)
            assert result["refund_id"] == "refund_1234567812345678"
            assert result["transaction_id"] == transaction_id
            assert result["status"] == "failed"
            assert result["currency"] == "BRL"