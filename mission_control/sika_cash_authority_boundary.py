"""Protected-data boundary for non-executing SIKA cash service-point review.

Records are supplied by a trusted server-side resolver, not by an HTTP client.
This helper performs no cash movement, authorisation writes or DB changes.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping

from . import sika_cash_service_point as cash


class CashAuthorityUnavailable(RuntimeError):
    """Authoritative service-point records were unavailable."""


def assess_with_trusted_records(
    *,
    intent_id: object,
    service_point_id: object,
    operator_id: object,
    customer_reference: object,
    amount: object,
    currency: object,
    direction: object,
    resolve_authority: Callable[[str, str], Mapping[str, object]],
) -> dict[str, object]:
    """Resolve permissions from a trusted service; caller approval flags ignored.

    The production resolver must authenticate its source, verify the current
    cashier-to-site assignment and financial permission, and deny on outages.
    """
    site = str(service_point_id or "").strip()
    operator = str(operator_id or "").strip()
    if not site or not operator:
        raise cash.CashServicePointError("cash_site_or_operator_required")
    try:
        evidence = resolve_authority(site, operator)
    except Exception as exc:
        raise CashAuthorityUnavailable("cash_authority_records_unavailable") from exc
    if not isinstance(evidence, Mapping):
        raise CashAuthorityUnavailable("cash_authority_records_invalid")
    if evidence.get("service_point_id") != site or evidence.get("operator_id") != operator:
        raise cash.CashServicePointError("cash_authority_identity_mismatch")
    return cash.assess_intent(
        intent_id=intent_id,
        service_point_id=site,
        operator_id=operator,
        customer_reference=customer_reference,
        amount=amount,
        currency=currency,
        direction=direction,
        staff_authorised=evidence.get("staff_authorised") is True,
        site_verified=evidence.get("site_verified") is True,
        regulated_cash_authority_proven=evidence.get("regulated_cash_authority_proven") is True,
    )


def assess_for_authenticated_operator(
    *,
    authenticated_operator_id: str,
    requested_operator_id: str,
    intent_id: object,
    service_point_id: object,
    customer_reference: object,
    amount: object,
    currency: object,
    direction: object,
) -> dict[str, object]:
    """Deny cashier substitution; caller must supply server-authenticated identity.

    This pure boundary is not a public endpoint or an authentication provider.
    """
    if not isinstance(authenticated_operator_id, str) or not authenticated_operator_id.strip():
        raise cash.CashServicePointError("cash_authenticated_operator_required")
    if authenticated_operator_id != requested_operator_id:
        raise cash.CashServicePointError("cash_operator_identity_mismatch")
    return assess_with_oap_store(
        intent_id=intent_id,
        service_point_id=service_point_id,
        authenticated_operator_id=authenticated_operator_id,
        customer_reference=customer_reference,
        amount=amount,
        currency=currency,
        direction=direction,
    )


def assess_with_oap_store(
    *,
    intent_id: object,
    service_point_id: object,
    authenticated_operator_id: object,
    session_operator_id: object,
    customer_reference: object,
    amount: object,
    currency: object,
    direction: object,
) -> dict[str, object]:
    """Use the canonical read-only OAP database resolver, not caller booleans.

    Only a trusted server-side caller may supply authenticated_operator_id.
    This is not an HTTP route, session verifier or cash execution endpoint.
    """
    from . import sika_cash_authority_store

    # Both identities must already be established by trusted server-side code.
    # A client-supplied operator ID cannot substitute for session identity.
    if (not str(session_operator_id or "").strip()
            or str(authenticated_operator_id or "").strip() != str(session_operator_id).strip()):
        raise cash.CashServicePointError("cash_authenticated_operator_mismatch")

    return assess_with_trusted_records(
        intent_id=intent_id,
        service_point_id=service_point_id,
        operator_id=authenticated_operator_id,
        customer_reference=customer_reference,
        amount=amount,
        currency=currency,
        direction=direction,
        resolve_authority=sika_cash_authority_store.resolve_authority,
    )
