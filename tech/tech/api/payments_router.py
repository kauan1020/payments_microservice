from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import os
from tech.infra.databases.database import get_session
from tech.interfaces.gateways.http_order_gateway import HttpOrderGateway  # Novo gateway HTTP
from tech.interfaces.repositories.payment_repository import PaymentRepository
from tech.infra.repositories.sql_alchemy_payment_repository import SQLAlchemyPaymentRepository
from tech.interfaces.schemas.payment_schema import PaymentCreate
from tech.use_cases.payments.create_payment_use_case import CreatePaymentUseCase
from tech.use_cases.payments.get_payment_status_use_case import GetPaymentStatusUseCase
from tech.use_cases.payments.webhook_payment_use_case import WebhookHandlerUseCase
from tech.interfaces.controllers.payment_controller import PaymentController

router = APIRouter()


def get_order_gateway() -> HttpOrderGateway:
    """
    Provides a configured HttpOrderGateway for communication with the orders service.

    Returns:
        HttpOrderGateway: Gateway configured with the orders service URL.
    """
    # Obter a URL do serviço de pedidos de variáveis de ambiente
    orders_service_url = os.getenv("SERVICE_ORDERS_URL", "http://host.docker.internal:8003")
    return HttpOrderGateway(base_url=orders_service_url)


def get_payment_repository(session: Session = Depends(get_session)) -> PaymentRepository:
    """
    Provides a configured payment repository instance.

    Args:
        session: SQLAlchemy database session.

    Returns:
        PaymentRepository: Repository for payment data operations.
    """
    return SQLAlchemyPaymentRepository(session)


def get_payment_controller(
        payment_repository: PaymentRepository = Depends(get_payment_repository),
        order_gateway: HttpOrderGateway = Depends(get_order_gateway)
) -> PaymentController:
    """
    Dependency injection for the PaymentController.

    Args:
        payment_repository: Repository for payment data operations.
        order_gateway: Gateway for communication with the orders service.

    Returns:
        PaymentController: Instance of PaymentController with required dependencies.
    """
    return PaymentController(
        create_payment_use_case=CreatePaymentUseCase(
            payment_repository=payment_repository,
            order_gateway=order_gateway
        ),
        get_payment_status_use_case=GetPaymentStatusUseCase(payment_repository),
        webhook_handler_use_case=WebhookHandlerUseCase(payment_repository),
    )


@router.post("/payments", status_code=201)
async def create_payment(payment_data: PaymentCreate,
                         controller: PaymentController = Depends(get_payment_controller)) -> dict:
    """
    Creates a new payment.

    Args:
        payment_data: The payment details to be created.
        controller: The PaymentController instance.

    Returns:
        The formatted response containing payment details.
    """
    return await controller.create_payment(payment_data)


@router.get("/payments/{order_id}")
def get_payment_status(order_id: int, controller: PaymentController = Depends(get_payment_controller)) -> dict:
    """
    Retrieves the payment status of an order.

    Args:
        order_id: The order ID.
        controller: The PaymentController instance.

    Returns:
        The formatted response containing payment status.
    """
    return controller.get_payment_status(order_id)


@router.post("/webhook")
def webhook_payment(order_id: int, status: str,
                    controller: PaymentController = Depends(get_payment_controller)) -> dict:
    """
    Handles payment status updates via webhook.

    Args:
        order_id: The order ID.
        status: The new payment status.
        controller: The PaymentController instance.

    Returns:
        The updated payment status.
    """
    return controller.webhook_payment(order_id, status)