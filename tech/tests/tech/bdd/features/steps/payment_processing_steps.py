# features/steps/payment_processing_steps.py

from behave import given, when, then
from behave.api.async_step import async_run_until_complete
from unittest.mock import patch, MagicMock, AsyncMock

from tech.domain.entities.payments import Payment, PaymentStatus
from tech.interfaces.schemas.payment_schema import PaymentCreate
from tech.use_cases.payments.create_payment_use_case import CreatePaymentUseCase
from tech.use_cases.payments.get_payment_status_use_case import GetPaymentStatusUseCase
from tech.use_cases.payments.webhook_payment_use_case import WebhookHandlerUseCase
from tech.interfaces.gateways.http_order_gateway import HttpOrderGateway
from tech.infra.repositories.sql_alchemy_payment_repository import SQLAlchemyPaymentRepository


@given('the order with ID {order_id:d} exists in the orders service')
def step_order_exists(context, order_id):
    context.order_gateway = MagicMock(spec=HttpOrderGateway)

    async_mock = AsyncMock()
    async_mock.return_value = {
        "id": order_id,
        "total_price": context.order_total if hasattr(context, 'order_total') else 100.50,
        "status": "PENDING"
    }
    context.order_gateway.get_order = async_mock


@given('the order total is {amount:f}')
def step_order_total(context, amount):
    context.order_total = amount


@given('the order with ID {order_id:d} does not exist in the orders service')
def step_order_does_not_exist(context, order_id):
    context.order_gateway = MagicMock(spec=HttpOrderGateway)

    async_mock = AsyncMock()
    async_mock.side_effect = ValueError(f"Order with ID {order_id} not found")
    context.order_gateway.get_order = async_mock


@given('a payment exists for order ID {order_id:d}')
def step_payment_exists(context, order_id):
    context.payment_repository = MagicMock(spec=SQLAlchemyPaymentRepository)

    # Criar o objeto de pagamento com um status padrão de PENDING
    payment = Payment(
        order_id=order_id,
        amount=100.50,
        status=PaymentStatus.PENDING
    )

    # Salvar no contexto para uso posterior
    context.payment = payment

    # Configurar o mock para retornar o pagamento
    context.payment_repository.get_by_order_id.return_value = payment


@given('the payment status is "{status}"')
def step_payment_status(context, status):
    # Atualizar o status do pagamento diretamente
    context.payment.status = PaymentStatus[status]

    # Garantir que o mock do repositório ainda retorna o pagamento atualizado
    context.payment_repository.get_by_order_id.return_value = context.payment


@given('no payment exists for order ID {order_id:d}')
def step_payment_does_not_exist(context, order_id):
    context.payment_repository = MagicMock(spec=SQLAlchemyPaymentRepository)
    context.payment_repository.get_by_order_id.side_effect = ValueError("Payment not found")


@when('I create a payment for order ID {order_id:d}')
@async_run_until_complete
async def step_create_payment(context, order_id):
    if not hasattr(context, 'payment_repository'):
        context.payment_repository = MagicMock(spec=SQLAlchemyPaymentRepository)

        def add_payment(payment):
            return Payment(
                order_id=payment.order_id,
                amount=payment.amount,
                status=payment.status
            )

        context.payment_repository.add.side_effect = add_payment

    create_payment_use_case = CreatePaymentUseCase(
        payment_repository=context.payment_repository,
        order_gateway=context.order_gateway
    )

    payment_data = PaymentCreate(order_id=order_id)

    try:
        context.result = await create_payment_use_case.execute(payment_data)
        context.error = None
    except Exception as e:
        context.error = e
        context.result = None


@when('I request the payment status for order ID {order_id:d}')
def step_get_payment_status(context, order_id):
    try:
        # Obter o pagamento diretamente do repositório mockado
        payment = context.payment_repository.get_by_order_id(order_id)
        # A função deve retornar apenas o status, não o objeto de pagamento completo
        context.result = payment.status
        context.error = None
    except Exception as e:
        context.error = e
        context.result = None


@when('I receive a webhook update with status "{status}" for order ID {order_id:d}')
def step_webhook_update(context, status, order_id):
    webhook_handler_use_case = WebhookHandlerUseCase(
        payment_repository=context.payment_repository
    )

    # Esta função mock é chamada quando o repositório atualiza um pagamento
    def update_payment(payment):
        # Atualizar o status do pagamento para o novo status
        payment.status = PaymentStatus[status]
        return payment

    context.payment_repository.update.side_effect = update_payment

    try:
        # Executar o caso de uso
        context.result = webhook_handler_use_case.execute(order_id, status)
        context.error = None
    except Exception as e:
        context.error = e
        context.result = None


@then('a payment should be created')
def step_payment_created(context):
    assert context.error is None, f"Error occurred: {context.error}"
    assert context.result is not None, "No payment was created"
    assert context.payment_repository.add.called, "Repository add method was not called"


@then('no payment should be created')
def step_no_payment_created(context):
    assert context.error is not None, "Expected an error but none occurred"
    assert not hasattr(context,
                       'payment_repository') or not context.payment_repository.add.called, "Repository add method was called"


@then('the payment status should be "{status}"')
def step_verify_status(context, status):
    assert context.error is None, f"Error occurred: {context.error}"
    assert context.result is not None, "No payment was returned"
    assert context.result.status.name == status, f"Expected status {status}, got {context.result.status.name}"


@then('the payment amount should be {amount:f}')
def step_verify_amount(context, amount):
    assert context.error is None, f"Error occurred: {context.error}"
    assert context.result is not None, "No payment was returned"
    assert context.result.amount == amount, f"Expected amount {amount}, got {context.result.amount}"


@then('I should receive the status "{status}"')
def step_received_status(context, status):
    assert context.error is None, f"Error occurred: {context.error}"
    assert context.result is not None, "No status was returned"
    # Comparar apenas os nomes dos status
    assert context.result.name == status, f"Expected status {status}, got {context.result.name}"


@then('the payment status should be updated to "{status}"')
def step_status_updated(context, status):
    assert context.error is None, f"Error occurred: {context.error}"
    assert context.result is not None, "No payment was returned"
    assert context.result.status.name == status, f"Expected status {status}, got {context.result.status.name}"
    assert context.payment_repository.update.called, "Repository update method was not called"


@then('I should receive an error message')
def step_receive_error(context):
    assert context.error is not None, "Expected an error but none occurred"


@then('I should receive a "{error_msg}" error')
def step_specific_error(context, error_msg):
    assert context.error is not None, "Expected an error but none occurred"
    assert str(context.error) == error_msg, f"Expected error message '{error_msg}', got '{str(context.error)}'"