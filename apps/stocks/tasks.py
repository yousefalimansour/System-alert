from decimal import Decimal
from celery import shared_task
from django.conf import settings
from django.utils import timezone
import httpx
import random
import logging
from apps.stocks.models import Stock, PriceSnapshot
from apps.alerts.utils import evaluate_alerts_for_stock
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

FMP_URL = "https://financialmodelingprep.com/api/v3/quote-short/{ticker}?apikey={apikey}"

@shared_task(bind=True, ignore_result=True)
def fetch_stock_prices(self):
    logger.info("=== FETCH_STOCK_PRICES TASK STARTED ===")
    
    apikey = getattr(settings, 'FMP_API_KEY', "") or getattr(settings, "TWELVE_API_KEY", "")
    logger.info(f"API Key present: {'Yes' if apikey else 'No'}")
    
    stocks = Stock.objects.all()
    logger.info(f"Found {stocks.count()} stocks to process")
    
    result = []
    client_timeout = httpx.Timeout(10.0, read=10.0)
    
    for stock in stocks:
        logger.info(f"Processing stock: {stock.ticker}")
        price = None
        try:
            if apikey:
                url = FMP_URL.format(ticker=stock.ticker, apikey=apikey)
                with httpx.Client(timeout=client_timeout) as client:
                    response = client.get(url)
                    response.raise_for_status()
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0 and 'price' in data[0]:
                        price = Decimal(str(data[0]['price']))
            else:
                # mock price when API key is not available
                price = Decimal(str(random.uniform(10, 1000)))
                logger.info(f"Using mock price for {stock.ticker}: {price}")
        except Exception as e:
            logger.error(f"Error fetching price for {stock.ticker}: {str(e)}")
            result.append({"ticker": stock.ticker, "error": str(e)})
            continue

        if price is not None:
            snap = PriceSnapshot.objects.create(
                stock=stock,
                price=price,
                timestamp=timezone.now()
            )
            logger.info(f"Created price snapshot for {stock.ticker}: {price}")
            result.append({"ticker": stock.ticker, "price": str(price)})
            
            # Evaluate alerts for this stock
            try:
                evaluate_alerts_for_stock(stock)
                logger.info(f"Evaluated alerts for {stock.ticker}")
            except Exception as e:
                logger.error(f"Error evaluating alerts for {stock.ticker}: {str(e)}")
        else:
            result.append({"ticker": stock.ticker, "skipped": True})

    logger.info(f"=== FETCH_STOCK_PRICES TASK COMPLETED. Processed {len(result)} stocks ===")
    return {"fetched": result}

@shared_task(bind=True, ignore_result=True)
def send_price_digest(self):
    logger.info("=== SEND_PRICE_DIGEST TASK STARTED ===")
    
    User = get_user_model()
    users = User.objects.filter(is_active=True, email__isnull=False).exclude(email='')
    logger.info(f"Found {users.count()} active users with email addresses")
    
    if users.count() == 0:
        logger.warning("No users found with email addresses!")
        return {"status": "no_users"}

    stocks = Stock.objects.all()
    logger.info(f"Found {stocks.count()} stocks for digest")
    
    rows = []
    for stock in stocks:
        snap = stock.snapshots.first()
        price = snap.price if snap else 'N/A'
        rows.append({'ticker': stock.ticker, 'price': price})
        logger.info(f"Stock {stock.ticker}: {price}")

    emails_sent = 0
    emails_failed = 0
    
    for user in users:
        logger.info(f"Preparing email for user: {user.username} ({user.email})")
        
        subject = "Daily Stock Price Digest"
        body = "Hello {},\n\nHere are the latest stock prices:\n\n".format(user.username)
        for r in rows:
            body += f"{r['ticker']}: {r['price']}\n"
        body += "\nRegards,\nStock Alerting System"
        
        try:
            logger.info(f"Attempting to send email to {user.email}")
            logger.info(f"Email settings - FROM: {settings.DEFAULT_FROM_EMAIL}")
            logger.info(f"Email settings - HOST: {settings.EMAIL_HOST}")
            logger.info(f"Email settings - HOST_USER: {settings.EMAIL_HOST_USER}")
            
            send_mail(
                subject, 
                body, 
                settings.DEFAULT_FROM_EMAIL, 
                [user.email], 
                fail_silently=False
            )
            logger.info(f"✅ Email sent successfully to {user.email}")
            emails_sent += 1
            
        except Exception as exc:
            logger.error(f"❌ Email send failed for {user.email}: {str(exc)}")
            emails_failed += 1

    logger.info(f"=== SEND_PRICE_DIGEST TASK COMPLETED. Sent: {emails_sent}, Failed: {emails_failed} ===")
    return {"emails_sent": emails_sent, "emails_failed": emails_failed}