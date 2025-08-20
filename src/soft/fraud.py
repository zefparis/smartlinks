
from __future__ import annotations
import re, time, hashlib
from typing import Dict

BAD_ASN = {'AS15169','AS14618','AS8075'}  # ex: Google/AWS/MS (exemple simplifié)
HEADLESS_UA = re.compile(r'Headless|Phantom|Puppeteer|Playwright', re.I)

def fingerprint(ip: str, ua: str, accept: str = '', tz: str = '') -> str:
    data = f"{ip}|{ua}|{accept}|{tz}".encode('utf-8')
    return hashlib.sha256(data).hexdigest()[:16]

def rules_score(ip: str, ua: str, ref: str = '') -> float:
    score = 0.0
    if HEADLESS_UA.search(ua or ''):
        score += 0.7
    if ref and 'bot' in ref.lower():
        score += 0.3
    return min(score, 1.0)

def velocity_score(count_ip_minute: int, uniq_fp_minute: int) -> float:
    # simple: trop de clics par minute sur une même IP => suspicieux
    if count_ip_minute >= 60:  # 1/s
        return 1.0
    if count_ip_minute >= 20:
        return 0.7
    if count_ip_minute >= 10:
        return 0.5
    return 0.1 if uniq_fp_minute > 1 else 0.2

def fraud_score(weights: Dict[str,float], rule_s: float, vel_s: float) -> float:
    wr = weights.get('rules', 0.4); wv = weights.get('velocity', 0.6)
    return max(0.0, min(1.0, wr*rule_s + wv*vel_s))
