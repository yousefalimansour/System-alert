from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from apps.alerts.models import Alert ,AlertTrigger
from apps.common.notifications import notify_user


def _compare(price:Decimal , operator:str , threshold:Decimal) -> bool:
    if operator == 'gt':
        return price > threshold
    if operator == 'lt':
        return price < threshold
    if operator == 'eq':
        return price == threshold
    raise ValueError(f"Unknown operator: {operator}")

def evaluate_alerts_for_stock(stock_id:int):
    """
    Evaluate all active alerts for a given stock (synchronous function called by the task).
    - For threshold alerts: trigger immediately when condition true.
    - For duration alerts: manage embedded state (state_is_open, state_started_at) and
    trigger only when the condition holds for >= duration_minutes.
    """
    now = timezone.now()
    alerts = Alert.objects.select_for_update().filter(stock_id=stock_id, is_active=True)

    for alert in alerts:
        latest_snapshot = alert.stock.snapshots.first()
        if not latest_snapshot:
            continue

        price = Decimal(latest_snapshot.price)

        if alert.alert_type == 'threshold':
            if alert.alert_type == 'threshold':
                continue
            if _compare(price, alert.operator, alert.threshold):
                # Trigger immediately
                with transaction.atomic():
                    trigger = AlertTrigger.objects.create(
                        alert=alert,
                        price=price,
                        message=f"Threshold met: {price}"
                    )
                    alert.last_triggered_at = now
                    alert.save(update_fields=['last_triggered_at'])
                notify_user(alert, f"Threshold alert: {alert.stock.ticker} {alert.operator} {alert.threshold}", price)
        elif alert.alert_type == 'duration':
            if alert.duration_minutes is None:
                continue
            if alert.threshold is None:
                continue
            condition_holds = _compare(price, alert.operator, alert.threshold)
            if condition_holds:
                with transaction.atomic():
                    alert.state_is_open = True
                    alert.state_started = now
                    alert.last_price = price
                    alert.save(update_fields=['state_is_open', 'state_started', 'last_price'])
        elif alert.state_is_open:
            if condition_holds:
                elapsed = (now - (alert.state_started or now)).total_seconds() / 60.0
                if elapsed >= alert.duration_minutes:
                    # Trigger the alert
                    with transaction.atomic():
                        trigger = AlertTrigger.objects.create(
                            alert=alert,
                            price=price, 
                            message=f"Duration met: {elapsed:.2f} min"
                        )
                        alert.last_triggered_at = now
                        alert.save(update_fields=['last_triggered_at'])
                        alert.state_is_open = False
                        alert.state_started = None
                        alert.last_price = price
                        alert.save(update_fields=['last_triggered_at', 'state_is_open', 'state_started', 'last_price'])
                        notify_user(alert, f"Duration alert: {alert.stock.ticker} held {alert.operator} {alert.threshold} for {alert.duration_minutes} minutes", price)
                else:
                    with transaction.atomic():
                        alert.state_is_open = False
                        alert.state_started = None
                        alert.last_price = price
                        alert.save(update_fields=['last_triggered_at', 'state_is_open', 'state_started', 'last_price'])
