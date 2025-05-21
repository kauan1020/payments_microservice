import pytest
from unittest.mock import Mock
from tech.interfaces.repositories.payment_repository import PaymentRepository
from tech.domain.entities.payments import Payment
from tech.interfaces.gateways.payment_gateway import PaymentGateway


class TestPaymentGateway:
    @pytest.fixture
    def repository_mock(self):
        return Mock(spec=PaymentRepository)

    @pytest.fixture
    def session_mock(self):
        return Mock()

    @pytest.fixture
    def gateway(self, session_mock, repository_mock):
        with pytest.MonkeyPatch.context() as monkeypatch:
            from tech.infra.repositories.sql_alchemy_payment_repository import SQLAlchemyPaymentRepository
            monkeypatch.setattr(
                'tech.interfaces.gateways.payment_gateway.SQLAlchemyPaymentRepository',
                Mock(return_value=repository_mock)
            )
            return PaymentGateway(session=session_mock)

    def test_init(self, session_mock, repository_mock):
        with pytest.MonkeyPatch.context() as monkeypatch:
            from tech.infra.repositories.sql_alchemy_payment_repository import SQLAlchemyPaymentRepository
            mock_sqlalchemy_repo = Mock(return_value=repository_mock)
            monkeypatch.setattr(
                'tech.interfaces.gateways.payment_gateway.SQLAlchemyPaymentRepository',
                mock_sqlalchemy_repo
            )

            gateway = PaymentGateway(session=session_mock)

            mock_sqlalchemy_repo.assert_called_once_with(session_mock)
            assert gateway.repository == repository_mock

    def test_add(self, gateway, repository_mock):
        payment = Mock(spec=Payment)
        repository_mock.add.return_value = payment

        result = gateway.add(payment)

        repository_mock.add.assert_called_once_with(payment)
        assert result == payment

    def test_get_by_order_id(self, gateway, repository_mock):
        order_id = 123
        payment = Mock(spec=Payment)
        repository_mock.get_by_order_id.return_value = payment

        result = gateway.get_by_order_id(order_id)

        repository_mock.get_by_order_id.assert_called_once_with(order_id)
        assert result == payment

    def test_update(self, gateway, repository_mock):
        payment = Mock(spec=Payment)
        repository_mock.update.return_value = payment

        result = gateway.update(payment)

        repository_mock.update.assert_called_once_with(payment)
        assert result == payment