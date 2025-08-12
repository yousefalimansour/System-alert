from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from apps.alerts.models import Alert, AlertTrigger
from apps.common.notifications import notify_user


def _compare(price: Decimal, operator: str, threshold: Decimal) -> bool:
    if operator == 'gt':
        return price > threshold
    if operator == 'lt':
        return price < threshold
    if operator == 'eq':
        return price == threshold
    raise ValueError(f"Unknown operator: {operator}")


def evaluate_alerts_for_stock(stock_id: int):
    """
    Evaluate active alerts for a stock.
    - threshold: trigger immediately when condition true.
    - duration: open state when condition holds, trigger after duration_minutes.
    """
    with transaction.atomic():
        alerts = Alert.objects.select_for_update().filter(stock_id=stock_id, is_active=True)
        now = timezone.now()

        for alert in alerts:
            latest_snapshot = alert.stock.snapshots.first()
            if not latest_snapshot:
                continue

            price = Decimal(latest_snapshot.price)

            if alert.alert_type == 'threshold':
                if alert.threshold is None:
                    continue
                if _compare(price, alert.operator, alert.threshold):
                    AlertTrigger.objects.create(
                        alert=alert,
                        price=price,
                        message=f"Threshold met: {price}"
                    )
                    alert.last_triggered_at = now
                    alert.last_price = price
                    alert.save(update_fields=['last_triggered_at', 'last_price'])
                    notify_user(
                        alert,
                        f"Threshold alert: {alert.stock.ticker} {alert.operator} {alert.threshold}",
                        price
                    )

            elif alert.alert_type == 'duration':
                if alert.duration_minutes is None or alert.threshold is None:
                    continue

                condition_holds = _compare(price, alert.operator, alert.threshold)

                if alert.state_is_open:
                    if condition_holds:
                        elapsed = (now - (alert.state_started or now)).total_seconds() / 60.0
                        if elapsed >= alert.duration_minutes:
                            AlertTrigger.objects.create(
                                alert=alert,
                                price=price,
                                message=f"Duration met: {elapsed:.2f} min"
                            )
                            alert.last_triggered_at = now
                            alert.state_is_open = False
                            alert.state_started = None
                            alert.last_price = price
                            alert.save(update_fields=['last_triggered_at', 'state_is_open', 'state_started', 'last_price'])
                            notify_user(
                                alert,
                                f"Duration alert: {alert.stock.ticker} held {alert.operator} {alert.threshold} for {alert.duration_minutes} minutes",
                                price
                            )
                        else:
                            alert.last_price = price
                            alert.save(update_fields=['last_price'])
                    else:
                        alert.state_is_open = False
                        alert.state_started = None
                        alert.last_price = price
                        alert.save(update_fields=['state_is_open', 'state_started', 'last_price'])
                else:
                    if condition_holds:
                        # Refresh from database to ensure we have the latest state
                        alert.refresh_from_db()
                        alert.state_is_open = True
                        alert.state_started = now
                        alert.last_price = price
                        alert.save(update_fields=['state_is_open', 'state_started', 'last_price'])
                    else:
                        alert.last_price = price
                        alert.save(update_fields=['last_price'])