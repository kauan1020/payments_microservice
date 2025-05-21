from tech.interfaces.gateways.http_order_gateway import HttpOrderGateway
from tech.interfaces.repositories.payment_repository import PaymentRepository
from tech.domain.entities.payments import Payment, PaymentStatus
from tech.interfaces.schemas.payment_schema import PaymentCreate


class CreatePaymentUseCase:
    """
    Use case for creating a payment.

    Handles the creation of payments by validating the order, calculating
    the amount, and storing the payment in the database. Communicates with
    the orders service via HTTP to obtain order details.
    """

    def __init__(
            self,
            payment_repository: PaymentRepository,
            order_gateway: HttpOrderGateway,
    ):
        """
        Initialize the CreatePaymentUseCase with dependencies.

        Args:
            payment_repository: Repository for storing payment data.
            order_gateway: Gateway for retrieving order information from the orders service.
        """
        self.payment_repository = payment_repository
        self.order_gateway = order_gateway

    async def execute(self, payment_data: PaymentCreate) -> Payment:
        """
        Create a new payment for an order.

        Retrieves order details from the orders service, creates a payment record
        with the appropriate amount, and stores it in the payment database.

        Args:
            payment_data: The payment data containing the order ID.

        Returns:
            The created payment with the initial status.

        Raises:
            ValueError: If the order is not found or communication fails.
        """
        try:
            # Obter detalhes do pedido via gateway HTTP
            order = await self.order_gateway.get_order(payment_data.order_id)

            # Extrair o valor total do pedido
            amount = order.get("total_price")
            if amount is None:
                raise ValueError("Order does not have a valid total price")

            # Criar entidade de pagamento
            payment = Payment(
                order_id=payment_data.order_id,
                amount=amount,
                status=PaymentStatus.PENDING,
            )

            # Salvar no repositório
            saved_payment = self.payment_repository.add(payment)
            return saved_payment

        except ValueError as e:
            # Repassar erros de valor (pedido não encontrado, etc.)
            raise e
        except Exception as e:
            # Converter outros erros em erros de valor com mensagem apropriada
            raise ValueError(f"Failed to create payment: {str(e)}")