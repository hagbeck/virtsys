import smtplib
from email.message import EmailMessage

import config_mailer as config


def mailer(sender='', receivers=None, subject='', message=''):

    if receivers is None:
        receivers = []

    if not sender or not receivers or not subject or not message:
        raise ValueError('Mail configuration not valid!')

    msg = EmailMessage()
    msg.set_content(message)

    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receivers

    # Send the message via our own SMTP server.
    s = smtplib.SMTP(config.TU_DORTMUND_SMTP['host'])
    s.send_message(msg)
    s.quit()
