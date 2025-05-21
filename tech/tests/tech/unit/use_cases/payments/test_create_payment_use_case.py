import pytest
from unittest.mock import Mock, AsyncMock, patch
from tech.interfaces.repositories.payment_repository import PaymentRepository
from tech.interfaces.gateways.http_order_gateway import HttpOrderGateway
from tech.domain.entities.payments import Payment, PaymentStatus
from tech.interfaces.schemas.payment_schema import PaymentCreate
from tech.use_cases.payments.create_payment_use_case import CreatePaymentUseCase


class TestCreatePaymentUseCase:
    @pytest.fixture
    def payment_repository_mock(self):
        return Mock(spec=PaymentRepository)

    @pytest.fixture
    def order_gateway_mock(self):
        return Mock(spec=HttpOrderGateway)

    @pytest.fixture
    def use_case(self, payment_repository_mock, order_gateway_mock):
        return CreatePaymentUseCase(
            payment_repository=payment_repository_mock,
            order_gateway=order_gateway_mock
        )

    @pytest.mark.asyncio
    async def test_execute_success(self, use_case, payment_repository_mock, order_gateway_mock):
        payment_data = PaymentCreate(order_id=123)
        order_mock = {"id": 123, "total_price": 100.0}

        order_gateway_mock.get_order = AsyncMock(return_value=order_mock)

        payment_mock = Mock(spec=Payment)
        payment_mock.order_id = 123
        payment_mock.amount = 100.0
        payment_mock.status = PaymentStatus.PENDING

        payment_repository_mock.add.return_value = payment_mock

        with patch('tech.use_cases.payments.create_payment_use_case.Payment') as mock_payment_class:
            mock_payment_class.return_value = payment_mock

            result = await use_case.execute(payment_data)

            order_gateway_mock.get_order.assert_called_once_with(123)

            mock_payment_class.assert_called_once_with(
                order_id=123,
                amount=100.0,
                status=PaymentStatus.PENDING
            )

            payment_repository_mock.add.assert_called_once_with(payment_mock)
            assert result == payment_mock

    @pytest.mark.asyncio
    async def test_execute_order_not_found(self, use_case, order_gateway_mock):
        payment_data = PaymentCreate(order_id=123)
        order_gateway_mock.get_order = AsyncMock(side_effect=ValueError("Order not found"))

        with pytest.raises(ValueError, match="Order not found"):
            await use_case.execute(payment_data)

            order_gateway_mock.get_order.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_execute_invalid_order_price(self, use_case, order_gateway_mock):
        payment_data = PaymentCreate(order_id=123)
        order_mock = {"id": 123}  # Missing total_price

        order_gateway_mock.get_order = AsyncMock(return_value=order_mock)

        with pytest.raises(ValueError, match="Order does not have a valid total price"):
            await use_case.execute(payment_data)

            order_gateway_mock.get_order.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_execute_repository_error(self, use_case, payment_repository_mock, order_gateway_mock):
        payment_data = PaymentCreate(order_id=123)
        order_mock = {"id": 123, "total_price": 100.0}

        order_gateway_mock.get_order = AsyncMock(return_value=order_mock)

        payment_mock = Mock(spec=Payment)
        payment_repository_mock.add.side_effect = Exception("Database error")

        with patch('tech.use_cases.payments.create_payment_use_case.Payment', return_value=payment_mock):
            with pytest.raises(ValueError, match="Failed to create payment: Database error"):
                await use_case.execute(payment_data)

                order_gateway_mock.get_order.assert_called_once_with(123)
                payment_repository_mock.add.assert_called_once_with(payment_mock)