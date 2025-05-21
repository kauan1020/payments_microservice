from fastapi import HTTPException
from tech.use_cases.payments.create_payment_use_case import CreatePaymentUseCase
from tech.use_cases.payments.get_payment_status_use_case import GetPaymentStatusUseCase
from tech.use_cases.payments.webhook_payment_use_case import WebhookHandlerUseCase
from tech.interfaces.presenters.payment_presenter import PaymentPresenter
from tech.interfaces.schemas.payment_schema import PaymentCreate
from tech.domain.entities.payments import PaymentStatus

class PaymentController:
    """
    Controller responsible for managing payment-related operations.
    """

    def __init__(
        self,
        create_payment_use_case: CreatePaymentUseCase,
        get_payment_status_use_case: GetPaymentStatusUseCase,
        webhook_handler_use_case: WebhookHandlerUseCase
    ):
        """
        Initializes the PaymentController with the required use cases.

        Args:
            create_payment_use_case (CreatePaymentUseCase): Use case for creating a payment.
            get_payment_status_use_case (GetPaymentStatusUseCase): Use case for retrieving payment status.
            webhook_handler_use_case (WebhookHandlerUseCase): Use case for handling webhook updates.
        """
        self.create_payment_use_case = create_payment_use_case
        self.get_payment_status_use_case = get_payment_status_use_case
        self.webhook_handler_use_case = webhook_handler_use_case

    async def create_payment(self, payment_data: PaymentCreate) -> dict:
        """
        Creates a new payment.

        Args:
            payment_data: The payment data containing the order ID.

        Returns:
            A formatted response containing the payment status.
        """
        try:
            payment = await self.create_payment_use_case.execute(payment_data)
            return PaymentPresenter.present_payment_status(payment.order_id, payment.status.value)
        except ValueError as e:
            raise ValueError(str(e))

    def get_payment_status(self, order_id: int) -> dict:
        """
        Retrieves the payment status of an order.

        Args:
            order_id (int): The ID of the order.

        Returns:
            dict: The formatted response containing payment status.

        Raises:
            HTTPException: If the payment is not found.
        """
        try:
            status = self.get_payment_status_use_case.execute(order_id)
            return PaymentPresenter.present_payment_status(order_id, status.name)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    def webhook_payment(self, order_id: int, status: str) -> dict:
        """
        Handles payment status updates via webhook.

        Args:
            order_id (int): The ID of the order.
            status (str): The new payment status.

        Returns:
            dict: The updated payment status.

        Raises:
            HTTPException: If the payment is not found or if the status is invalid.
        """
        try:
            payment_status = PaymentStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payment status")

        try:
            updated_payment = self.webhook_handler_use_case.execute(order_id, payment_status)
            return PaymentPresenter.present_payment_status(updated_payment.order_id, updated_payment.status.value)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
