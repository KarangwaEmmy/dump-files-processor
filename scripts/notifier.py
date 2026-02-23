import os
import json
import logging
import smtplib
from email.message import EmailMessage
import requests
from config import ALERT_LOG


def _write_alert_log(obj):
    try:
        ALERT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(ALERT_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(obj) + '\n')
    except Exception:
        logging.exception('Failed to write alert log')


def send_via_webhook(obj, webhook_url):
    try:
        r = requests.post(webhook_url, json=obj, timeout=5)
        return r.status_code >= 200 and r.status_code < 300
    except Exception:
        logging.exception('Webhook alert failed')
        return False


def send_via_email(obj, smtp_host, smtp_port, smtp_user, smtp_pass, from_addr, to_addrs):
    try:
        msg = EmailMessage()
        subj = obj.get('subject', 'Dump Listener Alert')
        msg['Subject'] = subj
        msg['From'] = from_addr
        msg['To'] = ','.join(to_addrs if isinstance(to_addrs, (list,tuple)) else [to_addrs])
        msg.set_content(json.dumps(obj, indent=2))

        with smtplib.SMTP(smtp_host, int(smtp_port or 25), timeout=10) as s:
            s.starttls()
            if smtp_user:
                s.login(smtp_user, smtp_pass)
            s.send_message(msg)
        return True
    except Exception:
        logging.exception('Email alert failed')
        return False


def send_alert(alert_obj):
    # Try webhook first, then email, then fallback to alert log
    webhook = os.environ.get('ALERT_WEBHOOK')
    if webhook:
        ok = send_via_webhook(alert_obj, webhook)
        if ok:
            return True

    smtp_host = os.environ.get('ALERT_SMTP_HOST')
    if smtp_host:
        ok = send_via_email(
            alert_obj,
            smtp_host,
            os.environ.get('ALERT_SMTP_PORT', 587),
            os.environ.get('ALERT_SMTP_USER'),
            os.environ.get('ALERT_SMTP_PASS'),
            os.environ.get('ALERT_FROM', 'alerts@example.com'),
            os.environ.get('ALERT_TO', 'admin@example.com').split(','),
        )
        if ok:
            return True

    # fallback
    _write_alert_log(alert_obj)
    return False
