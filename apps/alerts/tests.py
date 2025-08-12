# apps/alerts/tests.py
import pytest
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model
from freezegun import freeze_time

from apps.stocks.models import Stock, PriceSnapshot
from apps.alerts.models import Alert, AlertTrigger
from apps.alerts.utils import evaluate_alerts_for_stock


@pytest.fixture
def test_user(db):
    User = get_user_model()
    return User.objects.create_user(username='testuser', email='test@example.com', password='password')


@pytest.mark.django_db
def test_threshold_alert_triggers_immediately(monkeypatch, test_user):
    called = []

    def fake_notify(alert, message, price):
        called.append((alert.id, message, str(price)))

    monkeypatch.setattr('apps.alerts.utils.notify_user', fake_notify)

    stock = Stock.objects.create(ticker='TST', name='Test Inc.')
    alert = Alert.objects.create(
        user=test_user,
        stock=stock,
        alert_type='threshold',
        operator='gt',
        threshold=Decimal('100'),
        is_active=True
    )

    PriceSnapshot.objects.create(stock=stock, price=Decimal('150'), timestamp=timezone.now())

    evaluate_alerts_for_stock(stock.id)

    alert.refresh_from_db()
    assert AlertTrigger.objects.filter(alert=alert).exists()
    assert alert.last_triggered_at is not None
    assert len(called) == 1


@pytest.mark.django_db
def test_duration_alert_opens_and_then_triggers(monkeypatch, test_user):
    called = []

    def fake_notify(alert, message, price):
        called.append((alert.id, message, str(price)))

    monkeypatch.setattr('apps.alerts.utils.notify_user', fake_notify)

    stock = Stock.objects.create(ticker='DUR', name='Duration Inc.')
    alert = Alert.objects.create(
        user=test_user,
        stock=stock,
        alert_type='duration',
        operator='gt',
        threshold=Decimal('50'),
        duration_minutes=2,
        is_active=True
    )

    # time T0: condition holds -> should open state
    with freeze_time("2025-08-12 00:00:00"):
        PriceSnapshot.objects.create(stock=stock, price=Decimal('60'), timestamp=timezone.now())
        evaluate_alerts_for_stock(stock.id)
        alert.refresh_from_db()
        assert alert.state_is_open is True
        assert alert.state_started is not None

    # time T0 + 3 minutes: condition still holds -> should trigger and close state
    with freeze_time("2025-08-12 00:03:00"):
        PriceSnapshot.objects.create(stock=stock, price=Decimal('61'), timestamp=timezone.now())
        evaluate_alerts_for_stock(stock.id)

        alert.refresh_from_db()
        assert AlertTrigger.objects.filter(alert=alert).exists()
        assert alert.state_is_open is False
        assert len(called) == 1


@pytest.mark.django_db
def test_duration_alert_resets_if_condition_breaks(monkeypatch, test_user):
    called = []

    def fake_notify(alert, message, price):
        called.append((alert.id, message, str(price)))

    monkeypatch.setattr('apps.alerts.utils.notify_user', fake_notify)

    stock = Stock.objects.create(ticker='BRK', name='Break Inc.')
    alert = Alert.objects.create(
        user=test_user,
        stock=stock,
        alert_type='duration',
        operator='gt',
        threshold=Decimal('50'),
        duration_minutes=2,
        is_active=True
    )

    # T0: condition holds -> opens
    with freeze_time("2025-08-12 00:00:00"):
        PriceSnapshot.objects.create(stock=stock, price=Decimal('60'), timestamp=timezone.now())
        evaluate_alerts_for_stock(stock.id)
        alert.refresh_from_db()
        assert alert.state_is_open is True

    # T0 + 1 minute: condition breaks (price drops) -> should reset state and not trigger
    with freeze_time("2025-08-12 00:01:00"):
        PriceSnapshot.objects.create(stock=stock, price=Decimal('40'), timestamp=timezone.now())
        evaluate_alerts_for_stock(stock.id)
        alert.refresh_from_db()
        assert alert.state_is_open is False
        assert AlertTrigger.objects.filter(alert=alert).count() == 0
        assert len(called) == 0
