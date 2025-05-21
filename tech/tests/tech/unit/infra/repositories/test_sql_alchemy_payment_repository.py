import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from tech.domain.entities.payments import Payment, PaymentStatus
from tech.infra.repositories.sql_alchemy_payment_repository import SQLAlchemyPaymentRepository
from tech.infra.repositories.sql_alchemy_models import SQLAlchemyPayment


class TestSQLAlchemyPaymentRepository:
    @pytest.fixture
    def session_mock(self):
        return Mock(spec=Session)

    @pytest.fixture
    def repository(self, session_mock):
        return SQLAlchemyPaymentRepository(session_mock)

    @pytest.fixture
    def payment_data(self):
        return Payment(
            order_id=123,
            amount=100.5,
            status=PaymentStatus.PENDING
        )

    @pytest.fixture
    def db_payment(self):
        db_payment = Mock(spec=SQLAlchemyPayment)
        db_payment.id = 1
        db_payment.order_id = 123
        db_payment.amount = 100.5
        db_payment.status = "PENDING"
        return db_payment


    def test_to_db_payment(self, repository, payment_data):
        # Criar um mock personalizado para SQLAlchemyPayment que realmente retorna strings
        sql_payment_mock = MagicMock()
        sql_payment_mock.order_id = payment_data.order_id
        sql_payment_mock.amount = payment_data.amount
        sql_payment_mock.status = payment_data.status.name  # Garantir que seja string

        with patch('tech.infra.repositories.sql_alchemy_payment_repository.SQLAlchemyPayment',
                   return_value=sql_payment_mock):
            result = repository._to_db_payment(payment_data)

            assert result.order_id == payment_data.order_id
            assert result.amount == payment_data.amount
            assert isinstance(result.status, str)
            assert result.status == payment_data.status.name

    def test_add(self, repository, session_mock, payment_data, db_payment):
        session_mock.add.return_value = None
        session_mock.commit.return_value = None
        session_mock.refresh.return_value = None

        # Mock a criação do SQLAlchemyPayment para garantir o tipo correto de status
        db_payment.status = "PENDING"  # Explicitamente definir como string

        with patch('tech.infra.repositories.sql_alchemy_payment_repository.SQLAlchemyPayment', return_value=db_payment):
            with patch.object(repository, '_to_domain_payment', return_value=payment_data):
                result = repository.add(payment_data)

                session_mock.add.assert_called_once()
                session_mock.commit.assert_called_once()
                session_mock.refresh.assert_called_once()
                assert result == payment_data

    def test_get_by_order_id_found(self, repository, session_mock, db_payment, payment_data):
        query_mock = Mock()
        session_mock.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = db_payment

        with patch.object(repository, '_to_domain_payment', return_value=payment_data):
            result = repository.get_by_order_id(123)

            session_mock.query.assert_called_once_with(SQLAlchemyPayment)
            query_mock.filter.assert_called_once()
            query_mock.first.assert_called_once()
            assert result == payment_data

    def test_get_by_order_id_not_found(self, repository, session_mock):
        query_mock = Mock()
        session_mock.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None

        with pytest.raises(ValueError, match="Payment not found"):
            repository.get_by_order_id(999)

    def test_update(self, repository, session_mock, payment_data, db_payment):
        query_mock = Mock()
        session_mock.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = db_payment

        with patch.object(repository, '_to_domain_payment', return_value=payment_data):
            result = repository.update(payment_data)

            assert db_payment.amount == payment_data.amount
            assert db_payment.status == payment_data.status.name
            session_mock.commit.assert_called_once()
            session_mock.refresh.assert_called_once()
            assert result == payment_data

    def test_update_not_found(self, repository, session_mock, payment_data):
        query_mock = Mock()
        session_mock.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None

        with pytest.raises(ValueError, match="Payment not found"):
            repository.update(payment_data)

    def test_create(self, repository, session_mock, payment_data, db_payment):
        db_payment.id = 42
        session_mock.add.return_value = None
        session_mock.commit.return_value = None
        session_mock.refresh.return_value = None

        # Garantir que status é string
        db_payment.status = "PENDING"

        with patch('tech.infra.repositories.sql_alchemy_payment_repository.SQLAlchemyPayment', return_value=db_payment):
            result = repository.create(payment_data)

            session_mock.add.assert_called_once()
            session_mock.commit.assert_called_once()
            session_mock.refresh.assert_called_once()
            assert result.id == 42
            assert result == payment_data