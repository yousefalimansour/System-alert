# apps/stocks/tasks.py
from decimal import Decimal
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
import httpx
import random
import logging
from apps.stocks.models import Stock, PriceSnapshot
from apps.alerts.utils import evaluate_alerts_for_stock
from django.contrib.auth import get_user_model

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
        logger.info(f"Processing stock: {stock.ticker} (id={stock.id})")
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
                        logger.warning(f"No price in response for {stock.ticker}: {data}")
            else:
                # mock price when API key is not available
                price = Decimal(str(round(random.uniform(10, 1000), 2)))
                logger.info(f"Using mock price for {stock.ticker}: {price}")
        except Exception as e:
            logger.exception(f"Error fetching price for {stock.ticker}")
            result.append({"ticker": stock.ticker, "error": str(e)})
            continue

        if price is not None:
            try:
                snap = PriceSnapshot.objects.create(
                    stock=stock,
                    price=price,
                    timestamp=timezone.now()
                )
                logger.info(f"Created price snapshot for {stock.ticker}: {price}")
                result.append({"ticker": stock.ticker, "price": str(price)})

                # Evaluate alerts for this stock — pass stock.id (int)
                try:
                    evaluate_alerts_for_stock(stock.id)
                    logger.info(f"Evaluated alerts for {stock.ticker}")
                except Exception:
                    logger.exception(f"Error evaluating alerts for {stock.ticker}")
            except Exception:
                logger.exception(f"Error saving snapshot for {stock.ticker}")
                result.append({"ticker": stock.ticker, "error": "db_save_error"})
        else:
            result.append({"ticker": stock.ticker, "skipped": True})

    logger.info(f"=== FETCH_STOCK_PRICES TASK COMPLETED. Processed {len(result)} stocks ===")
    return {"fetched": result}


def generate_stock_digest_html(username, stock_data):
    stock_rows = ""
    for stock in stock_data:
        price_display = f"${stock['price']}" if stock['price'] != 'N/A' else 'N/A'
        stock_rows += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50;">
                {stock['ticker']}
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: right; color: #27ae60; font-weight: 600;">
                {price_display}
            </td>
        </tr>
        """

    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Stock Digest</title></head>
    <body style="font-family: Arial, sans-serif; background:#f8f9fa; margin:0; padding:20px;">
    <div style="max-width:600px; margin:0 auto; background:#fff; padding:0; border-radius:6px; overflow:hidden;">
      <div style="background:#34495e; padding:20px; color:#fff; text-align:center;">
        <h2 style="margin:0;">Daily Stock Digest</h2>
        <p style="margin:0;">{timezone.now().strftime('%B %d, %Y')}</p>
      </div>
      <div style="padding:20px;">
        <p>Hello <strong>{username}</strong>,</p>
        <p>Here are the latest stock prices from your watchlist:</p>
        <table style="width:100%; border-collapse:collapse;">
          <thead><tr style="background:#2c3e50; color:#fff;">
            <th style="text-align:left; padding:10px;">Stock Symbol</th>
            <th style="text-align:right; padding:10px;">Current Price</th>
          </tr></thead>
          <tbody>
            {stock_rows}
          </tbody>
        </table>
        <p style="margin-top:20px;">Best regards,<br>Stock Alerting System</p>
      </div>
    </div>
    </body></html>
    """
    return html_template


def generate_stock_digest_text(username, stock_data):
    text_content = f"Hello {username},\n\nHere are the latest stock prices from your watchlist:\n\n"
    text_content += "========================================\n"
    for stock in stock_data:
        price_display = f"${stock['price']}" if stock['price'] != 'N/A' else 'N/A'
        text_content += f"{stock['ticker']:10} : {price_display}\n"
    text_content += "\nReport generated on: " + timezone.now().strftime('%B %d, %Y at %I:%M %p') + "\n\nBest regards,\nStock Alerting System\n"
    return text_content


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
    
    # Prepare stock data
    stock_data = []
    for stock in stocks:
        snap = stock.snapshots.first()
        price = str(snap.price) if snap else 'N/A'
        stock_data.append({'ticker': stock.ticker, 'price': price})
        logger.info(f"Stock {stock.ticker}: {price}")

    emails_sent = 0
    emails_failed = 0
    
    for user in users:
        logger.info(f"Preparing email for user: {user.username} ({user.email})")
        
        try:
            subject = "Daily Stock Price Digest"
            html_content = generate_stock_digest_html(user.username, stock_data)
            text_content = generate_stock_digest_text(user.username, stock_data)
            
            logger.info(f"Attempting to send email to {user.email}")
            logger.info(f"Email settings - FROM: {settings.DEFAULT_FROM_EMAIL}")
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            send_result = email.send()
            logger.info(f"Email send result for {user.email}: {send_result}")
            if send_result:
                emails_sent += 1
            else:
                emails_failed += 1
                logger.error(f"EmailBackend reported failure sending to {user.email}")
            
        except Exception:
            logger.exception(f"❌ Email send failed for {user.email}")
            emails_failed += 1

    logger.info(f"=== SEND_PRICE_DIGEST TASK COMPLETED. Sent: {emails_sent}, Failed: {emails_failed} ===")
    return {"emails_sent": emails_sent, "emails_failed": emails_failed}
