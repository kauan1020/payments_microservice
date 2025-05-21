import pytest
from unittest.mock import Mock
from tech.interfaces.repositories.payment_repository import PaymentRepository
from tech.domain.entities.payments import Payment, PaymentStatus
from tech.use_cases.payments.webhook_payment_use_case import WebhookHandlerUseCase


class TestWebhookHandlerUseCase:
    @pytest.fixture
    def payment_repository_mock(self):
        return Mock(spec=PaymentRepository)

    @pytest.fixture
    def use_case(self, payment_repository_mock):
        return WebhookHandlerUseCase(payment_repository=payment_repository_mock)

    def test_execute_with_status_enum(self, use_case, payment_repository_mock):
        order_id = 123
        payment_status = PaymentStatus.APPROVED

        payment_mock = Mock(spec=Payment)
        payment_repository_mock.get_by_order_id.return_value = payment_mock
        payment_repository_mock.update.return_value = payment_mock

        result = use_case.execute(order_id, payment_status)

        payment_repository_mock.get_by_order_id.assert_called_once_with(order_id)
        assert payment_mock.status == payment_status
        payment_repository_mock.update.assert_called_once_with(payment_mock)
        assert result == payment_mock

    def test_execute_with_status_string(self, use_case, payment_repository_mock):
        order_id = 123
        payment_status = "APPROVED"

        payment_mock = Mock(spec=Payment)
        payment_repository_mock.get_by_order_id.return_value = payment_mock
        payment_repository_mock.update.return_value = payment_mock

        result = use_case.execute(order_id, payment_status)

        payment_repository_mock.get_by_order_id.assert_called_once_with(order_id)
        assert payment_mock.status == PaymentStatus.APPROVED
        payment_repository_mock.update.assert_called_once_with(payment_mock)
        assert result == payment_mock

    def test_execute_with_invalid_status(self, use_case):
        order_id = 123
        payment_status = "INVALID_STATUS"

        with pytest.raises(ValueError, match=f"Invalid payment status: {payment_status}"):
            use_case.execute(order_id, payment_status)

    def test_execute_payment_not_found(self, use_case, payment_repository_mock):
        order_id = 123
        payment_status = PaymentStatus.APPROVED

        payment_repository_mock.get_by_order_id.return_value = None

        with pytest.raises(ValueError, match="Payment not found for this order."):
            use_case.execute(order_id, payment_status)

            payment_repository_mock.get_by_order_id.assert_called_once_with(order_id)