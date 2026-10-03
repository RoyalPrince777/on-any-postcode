"""Read-only OAP Bank Intelligence catalog.

This module only describes first-party intelligence domains already present in
the repository. It cannot authorize activity, call providers, post journals,
settle funds, or move money.
"""

DOMAINS = (
    ("accounts", "Accounts"),
    ("payments", "Payments"),
    ("disputes", "Disputes"),
    ("submission", "Submission Evidence"),
    ("financial", "Financial Intelligence"),
    ("statements", "Financial Statements"),
    ("accounting", "Accounting Intelligence"),
    ("double-entry", "Double Entry"),
    ("journal", "Journal Integrity"),
    ("blockchain", "Blockchain Integrity"),
    ("cards", "Card Controls"),
    ("treasury", "Treasury and Liquidity"),
    ("alm", "ALM Forecasting"),
    ("reconciliation", "Runtime Reconciliation"),
    ("exceptions", "Reconciliation Exceptions"),
    ("refunds", "Refund Intelligence"),
    ("multi-currency", "Multi-Currency Revaluation"),
    ("intercompany", "Intercompany Accounting"),
    ("risk", "Risk Intelligence"),
    ("rights", "Rights and Remedy"),
    ("regulated-gates", "Regulated Evidence Gates"),
)


def status():
    return {
        "system": "OAP Bank Intelligence",
        "domain_count": len(DOMAINS),
        "domains": [{"id": key, "name": name} for key, name in DOMAINS],
        "advisory_only": True,
        "execution_authority": False,
        "provider_calling": False,
        "journal_posting": False,
        "settlement_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }
