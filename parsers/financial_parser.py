"""
Financial Intelligence & Transaction Ledger Parser for aforensic.
Extracts and analyzes bank SMS alerts, OTPs, mobile wallets (eSewa, Khalti, Google Pay, PhonePe, Paytm),
and digital banking notifications into a structured forensic audit ledger.
"""

import re
from typing import List, Dict, Any, Optional


class FinancialParser:
    def __init__(self):
        # Transaction categorization regexes
        self.debit_patterns = [
            r'(?:debited|spent|paid|withdrawn|transferred to|sent to|deducted|purchased|txn of)\s*(?:by|for|of)?\s*(?:Rs\.?|NPR|INR|USD|\$|EUR|€|GBP|£)?\s*([\d,]+(?:\.\d{1,2})?)',
            r'(?:Rs\.?|NPR|INR|USD|\$|EUR|€|GBP|£)\s*([\d,]+(?:\.\d{1,2})?)\s*(?:debited|spent|paid|deducted|withdrawn|sent)'
        ]
        self.credit_patterns = [
            r'(?:credited|received|deposited|refunded|cashback of|added to)\s*(?:with|of)?\s*(?:Rs\.?|NPR|INR|USD|\$|EUR|€|GBP|£)?\s*([\d,]+(?:\.\d{1,2})?)',
            r'(?:Rs\.?|NPR|INR|USD|\$|EUR|€|GBP|£)\s*([\d,]+(?:\.\d{1,2})?)\s*(?:credited|deposited|received|refunded)'
        ]
        self.otp_patterns = [
            r'\b(?:OTP|code|verification code|security code|passcode|one time password)\s*(?:is|:)?\s*([0-9]{4,8})\b',
            r'\b([0-9]{4,8})\s*(?:is your (?:OTP|secret OTP|verification code))\b'
        ]
        self.balance_patterns = [
            r'(?:bal|balance|avl bal|avail bal|available balance)\s*(?:is|:)?\s*(?:Rs\.?|NPR|INR|USD|\$|EUR|€|GBP|£)?\s*([\d,]+(?:\.\d{1,2})?)'
        ]
        self.account_patterns = [
            r'(?:a\/c|acct|account|card)\s*(?:no\.?|ending in|ending)?\s*([a-zA-Z0-9*xX]{3,16})'
        ]

    def parse_message_text(self, text: str, timestamp: str = "N/A", source: str = "SMS") -> Optional[Dict[str, Any]]:
        """
        Analyzes a single message or notification body for financial transaction metadata.
        """
        if not text or len(text) < 5:
            return None

        # Check for OTP
        otp_code = None
        for pat in self.otp_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                otp_code = m.group(1)
                break

        # Check for Debit
        debit_amount = None
        for pat in self.debit_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                raw_amt = m.group(1).replace(",", "")
                try:
                    debit_amount = float(raw_amt)
                    break
                except ValueError:
                    pass

        # Check for Credit
        credit_amount = None
        for pat in self.credit_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                raw_amt = m.group(1).replace(",", "")
                try:
                    credit_amount = float(raw_amt)
                    break
                except ValueError:
                    pass

        # If not financial or OTP, ignore
        if not debit_amount and not credit_amount and not otp_code:
            # Check for wallet keywords
            wallet_keywords = ["esewa", "khalti", "paytm", "phonepe", "gpay", "google pay", "paypal", "remit", "western union", "moneygram", "nabil", "nic asia", "chase", "wells fargo"]
            if not any(k in text.lower() for k in wallet_keywords):
                return None

        # Extract balance
        balance = None
        for pat in self.balance_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                try:
                    balance = float(m.group(1).replace(",", ""))
                    break
                except ValueError:
                    pass

        # Extract account number
        account_no = "N/A"
        for pat in self.account_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                account_no = m.group(1)
                break

        # Extract currency
        currency = "NPR/INR/USD"
        if "$" in text or "USD" in text:
            currency = "USD"
        elif "Rs" in text or "NPR" in text:
            currency = "NPR"
        elif "INR" in text or "₹" in text:
            currency = "INR"
        elif "€" in text or "EUR" in text:
            currency = "EUR"
        elif "£" in text or "GBP" in text:
            currency = "GBP"

        # Determine transaction type
        txn_type = "Informational / Other"
        amount = 0.0
        if otp_code:
            txn_type = "OTP / 2FA Verification"
        elif debit_amount:
            txn_type = "DEBIT / Outgoing"
            amount = debit_amount
        elif credit_amount:
            txn_type = "CREDIT / Incoming"
            amount = credit_amount

        return {
            "type": txn_type,
            "amount": amount,
            "currency": currency,
            "otp_code": otp_code or "",
            "account_ref": account_no,
            "balance": balance if balance is not None else "N/A",
            "timestamp": timestamp,
            "message_text": text[:300],
            "source": source
        }

    def parse_corpus(self, sms_list: List[Dict[str, Any]], notifications_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parses full SMS and notification corpora to produce an enterprise financial ledger summary.
        """
        ledger = []
        total_debit = 0.0
        total_credit = 0.0
        otp_count = 0

        # Process SMS
        for sms in sms_list:
            body = sms.get("body", "")
            ts = sms.get("timestamp", "N/A")
            res = self.parse_message_text(body, ts, source=f"SMS ({sms.get('address', 'Unknown')})")
            if res:
                ledger.append(res)
                if res["type"] == "DEBIT / Outgoing":
                    total_debit += res["amount"]
                elif res["type"] == "CREDIT / Incoming":
                    total_credit += res["amount"]
                elif res["type"] == "OTP / 2FA Verification":
                    otp_count += 1

        # Process Notifications
        for notif in notifications_list:
            combined_text = f"{notif.get('title', '')} {notif.get('body', '')}"
            ts = notif.get("timestamp", "N/A")
            res = self.parse_message_text(combined_text, ts, source=f"Notification ({notif.get('package', 'App')})")
            if res:
                ledger.append(res)
                if res["type"] == "DEBIT / Outgoing":
                    total_debit += res["amount"]
                elif res["type"] == "CREDIT / Incoming":
                    total_credit += res["amount"]
                elif res["type"] == "OTP / 2FA Verification":
                    otp_count += 1

        return {
            "summary": {
                "total_transactions": len(ledger),
                "total_debit_amount": round(total_debit, 2),
                "total_credit_amount": round(total_credit, 2),
                "otp_codes_captured": otp_count
            },
            "ledger": ledger
        }
