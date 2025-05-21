import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from tech.domain.entities.payments import Payment, PaymentStatus
from tech.interfaces.presenters.payment_presenter import PaymentPresenter
from tech.interfaces.schemas.payment_schema import PaymentCreate
from tech.interfaces.controllers.payment_controller import PaymentController


class TestPaymentController:
    @pytest.fixture
    def create_payment_use_case_mock(self):
        mock = Mock()
        # Converter o método execute para um AsyncMock
        mock.execute = AsyncMock()
        return mock

    @pytest.fixture
    def get_payment_status_use_case_mock(self):
        return Mock()

    @pytest.fixture
    def webhook_handler_use_case_mock(self):
        return Mock()

    @pytest.fixture
    def controller(self, create_payment_use_case_mock, get_payment_status_use_case_mock, webhook_handler_use_case_mock):
        return PaymentController(
            create_payment_use_case=create_payment_use_case_mock,
            get_payment_status_use_case=get_payment_status_use_case_mock,
            webhook_handler_use_case=webhook_handler_use_case_mock
        )

    @pytest.mark.asyncio
    async def test_create_payment_success(self, controller, create_payment_use_case_mock):
        payment_data = PaymentCreate(order_id=123)
        mock_payment = Payment(order_id=123, amount=100.0, status=PaymentStatus.PENDING)
        create_payment_use_case_mock.execute.return_value = mock_payment

        with patch.object(PaymentPresenter, 'present_payment_status',
                          return_value={"order_id": 123, "status": "PENDING"}) as mock_present:
            result = await controller.create_payment(payment_data)

            create_payment_use_case_mock.execute.assert_awaited_once_with(payment_data)
            mock_present.assert_called_once_with(123, "PENDING")
            assert result == {"order_id": 123, "status": "PENDING"}

    @pytest.mark.asyncio
    async def test_create_payment_error(self, controller, create_payment_use_case_mock):
        payment_data = PaymentCreate(order_id=123)
        create_payment_use_case_mock.execute.side_effect = ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await controller.create_payment(payment_data)

            create_payment_use_case_mock.execute.assert_awaited_once_with(payment_data)

    def test_get_payment_status_success(self, controller, get_payment_status_use_case_mock):
        order_id = 123
        get_payment_status_use_case_mock.execute.return_value = PaymentStatus.APPROVED

        with patch.object(PaymentPresenter, 'present_payment_status',
                          return_value={"order_id": 123, "status": "APPROVED"}) as mock_present:
            result = controller.get_payment_status(order_id)

            get_payment_status_use_case_mock.execute.assert_called_once_with(order_id)
            mock_present.assert_called_once_with(order_id, "APPROVED")
            assert result == {"order_id": 123, "status": "APPROVED"}

    def test_get_payment_status_not_found(self, controller, get_payment_status_use_case_mock):
        order_id = 123
        get_payment_status_use_case_mock.execute.side_effect = ValueError("Payment not found")

        with pytest.raises(HTTPException) as excinfo:
            controller.get_payment_status(order_id)

        get_payment_status_use_case_mock.execute.assert_called_once_with(order_id)
        assert excinfo.value.status_code == 404
        assert excinfo.value.detail == "Payment not found"

    def test_webhook_payment_success(self, controller, webhook_handler_use_case_mock):
        order_id = 123
        status = "APPROVED"
        mock_payment = Payment(order_id=123, amount=100.0, status=PaymentStatus.APPROVED)
        webhook_handler_use_case_mock.execute.return_value = mock_payment

        with patch.object(PaymentPresenter, 'present_payment_status',
                          return_value={"order_id": 123, "status": "APPROVED"}) as mock_present:
            result = controller.webhook_payment(order_id, status)

            webhook_handler_use_case_mock.execute.assert_called_once_with(order_id, PaymentStatus.APPROVED)
            mock_present.assert_called_once_with(order_id, "APPROVED")
            assert result == {"order_id": 123, "status": "APPROVED"}

    def test_webhook_payment_invalid_status(self, controller):
        order_id = 123
        status = "INVALID_STATUS"

        with pytest.raises(HTTPException) as excinfo:
            controller.webhook_payment(order_id, status)

        assert excinfo.value.status_code == 400
        assert excinfo.value.detail == "Invalid payment status"

    def test_webhook_payment_not_found(self, controller, webhook_handler_use_case_mock):
        order_id = 123
        status = "APPROVED"
        webhook_handler_use_case_mock.execute.side_effect = ValueError("Payment not found")

        with pytest.raises(HTTPException) as excinfo:
            controller.webhook_payment(order_id, status)

        webhook_handler_use_case_mock.execute.assert_called_once_with(order_id, PaymentStatus.APPROVED)
        assert excinfo.value.status_code == 404
        assert excinfo.value.detail == "Payment not found"