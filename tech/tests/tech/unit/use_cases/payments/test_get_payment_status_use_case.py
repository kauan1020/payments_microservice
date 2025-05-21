import pytest
from unittest.mock import Mock
from tech.interfaces.repositories.payment_repository import PaymentRepository
from tech.domain.entities.payments import Payment, PaymentStatus
from tech.use_cases.payments.get_payment_status_use_case import GetPaymentStatusUseCase


class TestGetPaymentStatusUseCase:
    @pytest.fixture
    def payment_repository_mock(self):
        return Mock(spec=PaymentRepository)

    @pytest.fixture
    def use_case(self, payment_repository_mock):
        return GetPaymentStatusUseCase(payment_repository=payment_repository_mock)

    def test_execute_success(self, use_case, payment_repository_mock):
        order_id = 123
        payment_mock = Mock(spec=Payment)
        payment_mock.status = PaymentStatus.APPROVED

        payment_repository_mock.get_by_order_id.return_value = payment_mock

        result = use_case.execute(order_id)

        payment_repository_mock.get_by_order_id.assert_called_once_with(order_id)
        assert result == PaymentStatus.APPROVED

    def test_execute_payment_not_found(self, use_case, payment_repository_mock):
        order_id = 123
        payment_repository_mock.get_by_order_id.return_value = None

        with pytest.raises(ValueError, match="Payment not found for the given order ID."):
            use_case.execute(order_id)

            payment_repository_mock.get_by_order_id.assert_called_once_with(order_id)