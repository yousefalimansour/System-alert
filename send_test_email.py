from django.core.mail import send_mail

send_mail(
    subject='SMTP Test Email',
    message='Hello Yousef, this is a test from SMTP.',
    from_email='moradyousef954@gmail.com',
    recipient_list=['moradyousef954@gmail.com'],
    fail_silently=False,
)
