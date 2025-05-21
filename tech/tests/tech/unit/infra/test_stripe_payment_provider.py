import pytest
from unittest.mock import Mock, patch, AsyncMock
import stripe
from tech.infra.stripe_payment_provider import StripePaymentProvider


class TestStripePaymentProvider:
    @pytest.fixture
    def provider(self):
        with patch('stripe.api_key', None):
            return StripePaymentProvider("test_api_key")

    def test_init(self):
        with patch('stripe.api_key', None):
            provider = StripePaymentProvider("test_api_key")

            assert provider.api_key == "test_api_key"
            assert stripe.api_key == "test_api_key"

    @pytest.mark.asyncio
    async def test_process_payment_success(self, provider):
        order_id = 123
        amount = 100.50
        payment_method = "card"

        mock_intent = AsyncMock()
        mock_intent.id = "pi_test_id"
        mock_intent.status = "succeeded"

        with patch('stripe.PaymentIntent.create', AsyncMock(return_value=mock_intent)) as mock_create:
            result = await provider.process_payment(order_id, amount, payment_method)

            mock_create.assert_called_once_with(
                amount=10050,  # 100.50 converted to cents
                currency="brl",
                payment_method_types=["card"],
                metadata={"order_id": "123"}
            )

            assert result["transaction_id"] == "pi_test_id"
            assert result["status"] == "succeeded"
            assert result["amount"] == amount
            assert result["currency"] == "BRL"

    @pytest.mark.asyncio
    async def test_process_payment_stripe_error(self, provider):
        order_id = 123
        amount = 100.50
        payment_method = "card"

        error = stripe.error.StripeError("Test error")
        with patch('stripe.PaymentIntent.create', AsyncMock(side_effect=error)) as mock_create:
            with pytest.raises(Exception, match="Stripe payment processing error: Test error"):
                await provider.process_payment(order_id, amount, payment_method)

            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_payment_generic_error(self, provider):
        order_id = 123
        amount = 100.50
        payment_method = "card"

        error = Exception("Generic error")
        with patch('stripe.PaymentIntent.create', AsyncMock(side_effect=error)) as mock_create:
            with pytest.raises(Exception, match="Error processing payment: Generic error"):
                await provider.process_payment(order_id, amount, payment_method)

            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_refund_payment_full_amount(self, provider):
        transaction_id = "pi_test_id"

        mock_refund = AsyncMock()
        mock_refund.id = "re_test_id"
        mock_refund.status = "succeeded"
        mock_refund.amount = 10050  # 100.50 in cents

        with patch('stripe.Refund.create', AsyncMock(return_value=mock_refund)) as mock_create:
            result = await provider.refund_payment(transaction_id)

            mock_create.assert_called_once_with(payment_intent=transaction_id)

            assert result["refund_id"] == "re_test_id"
            assert result["transaction_id"] == transaction_id
            assert result["status"] == "succeeded"
            assert result["amount"] == 100.50  # converted from cents

    @pytest.mark.asyncio
    async def test_refund_payment_partial_amount(self, provider):
        transaction_id = "pi_test_id"
        amount = 50.25

        mock_refund = AsyncMock()
        mock_refund.id = "re_test_id"
        mock_refund.status = "succeeded"
        mock_refund.amount = 5025  # 50.25 in cents

        with patch('stripe.Refund.create', AsyncMock(return_value=mock_refund)) as mock_create:
            result = await provider.refund_payment(transaction_id, amount)

            mock_create.assert_called_once_with(payment_intent=transaction_id, amount=5025)

            assert result["refund_id"] == "re_test_id"
            assert result["transaction_id"] == transaction_id
            assert result["status"] == "succeeded"
            assert result["amount"] == amount

    @pytest.mark.asyncio
    async def test_refund_payment_stripe_error(self, provider):
        transaction_id = "pi_test_id"

        error = stripe.error.StripeError("Test error")
        with patch('stripe.Refund.create', AsyncMock(side_effect=error)) as mock_create:
            with pytest.raises(Exception, match="Stripe refund processing error: Test error"):
                await provider.refund_payment(transaction_id)

            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_refund_payment_generic_error(self, provider):
        transaction_id = "pi_test_id"

        error = Exception("Generic error")
        with patch('stripe.Refund.create', AsyncMock(side_effect=error)) as mock_create:
            with pytest.raises(Exception, match="Error processing refund: Generic error"):
                await provider.refund_payment(transaction_id)

            mock_create.assert_called_once()