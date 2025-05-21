import pytest
from tech.interfaces.presenters.payment_presenter import PaymentPresenter


class TestPaymentPresenter:
    def test_present_payment_status(self):
        order_id = 123
        status = "APPROVED"

        result = PaymentPresenter.present_payment_status(order_id, status)

        assert result == {
            "order_id": order_id,
            "status": status
        }

    def test_present_payment_status_with_different_values(self):
        order_id = 456
        status = "PENDING"

        result = PaymentPresenter.present_payment_status(order_id, status)

        assert result == {
            "order_id": order_id,
            "status": status
        }