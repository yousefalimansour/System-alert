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

def generate_stock_digest_html(username, stock_data):
    """Generate HTML template for stock digest email"""
    
    # Generate stock rows HTML
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
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Daily Stock Digest</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 300; letter-spacing: 1px;">
                    📈 Daily Stock Digest
                </h1>
                <p style="color: #e8f1ff; margin: 10px 0 0 0; font-size: 16px;">
                    {timezone.now().strftime('%B %d, %Y')}
                </p>
            </div>
            
            <!-- Greeting -->
            <div style="padding: 30px 30px 20px 30px;">
                <p style="color: #2c3e50; font-size: 18px; margin: 0; line-height: 1.5;">
                    Hello <strong>{username}</strong>,
                </p>
                <p style="color: #7f8c8d; font-size: 16px; margin: 15px 0 0 0; line-height: 1.6;">
                    Here are the latest stock prices from your watchlist:
                </p>
            </div>
            
            <!-- Stock Table -->
            <div style="padding: 0 30px 30px 30px;">
                <table style="width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <thead>
                        <tr style="background-color: #34495e;">
                            <th style="padding: 16px; text-align: left; color: #ffffff; font-weight: 600; font-size: 16px; letter-spacing: 0.5px;">
                                Stock Symbol
                            </th>
                            <th style="padding: 16px; text-align: right; color: #ffffff; font-weight: 600; font-size: 16px; letter-spacing: 0.5px;">
                                Current Price
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {stock_rows}
                    </tbody>
                </table>
            </div>
            
            <!-- Footer -->
            <div style="background-color: #ecf0f1; padding: 25px 30px; text-align: center; border-top: 3px solid #3498db;">
                <p style="color: #7f8c8d; font-size: 14px; margin: 0; line-height: 1.5;">
                    Best regards,<br>
                    <strong style="color: #2c3e50;">Stock Alerting System</strong>
                </p>
                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #bdc3c7;">
                    <p style="color: #95a5a6; font-size: 12px; margin: 0;">
                        This is an automated message. Please do not reply to this email.
                    </p>
                </div>
            </div>
            
        </div>
    </body>
    </html>
    """
    
    return html_template

def generate_stock_digest_text(username, stock_data):
    """Generate plain text version for stock digest email"""
    
    text_content = f"""Hello {username},

Here are the latest stock prices from your watchlist:

"""
    
    # Add stock data
    text_content += "STOCK PRICES\n"
    text_content += "=" * 50 + "\n"
    
    for stock in stock_data:
        price_display = f"${stock['price']}" if stock['price'] != 'N/A' else 'N/A'
        text_content += f"{stock['ticker']:10} : {price_display}\n"
    
    text_content += "\n" + "=" * 50
    text_content += f"""

Report generated on: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}

Best regards,
Stock Alerting System

---
This is an automated message. Please do not reply to this email.
    """
    
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
        price = snap.price if snap else 'N/A'
        stock_data.append({'ticker': stock.ticker, 'price': price})
        logger.info(f"Stock {stock.ticker}: {price}")

    emails_sent = 0
    emails_failed = 0
    
    for user in users:
        logger.info(f"Preparing email for user: {user.username} ({user.email})")
        
        try:
            # Generate email content
            subject = "Daily Stock Price Digest"
            html_content = generate_stock_digest_html(user.username, stock_data)
            text_content = generate_stock_digest_text(user.username, stock_data)
            
            logger.info(f"Attempting to send email to {user.email}")
            logger.info(f"Email settings - FROM: {settings.DEFAULT_FROM_EMAIL}")
            logger.info(f"Email settings - HOST: {settings.EMAIL_HOST}")
            logger.info(f"Email settings - HOST_USER: {settings.EMAIL_HOST_USER}")
            
            # Create email with both HTML and text versions
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"✅ Email sent successfully to {user.email}")
            emails_sent += 1
            
        except Exception as exc:
            logger.error(f"❌ Email send failed for {user.email}: {str(exc)}")
            emails_failed += 1

    logger.info(f"=== SEND_PRICE_DIGEST TASK COMPLETED. Sent: {emails_sent}, Failed: {emails_failed} ===")
    return {"emails_sent": emails_sent, "emails_failed": emails_failed}