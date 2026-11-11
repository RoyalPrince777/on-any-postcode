#!/usr/bin/env python3
"""Apply SIKA browser/Store navigation to an existing modified KORADASO checkout.

Non-destructive: targets only existing source files, refuses ambiguous anchors,
and writes nothing unless every target can be safely prepared. Creates timestamped
file backups. Does not provision accounts, touch Arena, restart Flask or deploy.
"""
from __future__ import annotations

import argparse
import datetime
from pathlib import Path
import shutil
import sys

FILES = {
    "mission_control/oap_store.py": "store",
    "mission_control/templates/oap_store.html": "store_html",
    "mission_control/templates/oap_bank_store_detail.html": "detail_html",
    "mission_control/templates/oap_pay_bank.html": "bank_html",
}


def replace_once(source: str, old: str, new: str, *, name: str) -> str:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"{name}: expected one anchor; found {count}")
    return source.replace(old, new, 1)


def apply_store(source: str) -> str:
    if "def _bank_information_entry()" not in source:
        import_old = "from . import oap_store_registry, products"
        import_new = "from . import bank_store_listing, oap_store_registry, products"
        if import_new not in source:
            source = replace_once(source, import_old, import_new, name="store import")
        anchor = "def catalogue() -> tuple[dict[str, object], ...]:"
        helper = '''def _bank_information_entry() -> dict[str, object]:
    """Existing SIKA bank listing, browser-only, no install or finance actions."""
    bank = bank_store_listing.listing()
    return {
        "app_id": bank["app_id"],
        "name": bank["name"],
        "publisher": bank["publisher"],
        "distribution": "OAP Store",
        "first_party": True,
        "description": bank["description"],
        "release_state": "release_pending",
        "install_enabled": False,
        "install_mode": "Information only",
        "manifest_url": None,
        "service_worker_url": None,
        "start_url": None,
        "open_url": "/oap-store/apps/oap.usa_royalty_bank/view",
        "browser_url": "/pay/bank",
        "browser_account_url": "/pay/bank/me",
        "category": "Value",
        "install_url": None,
        "offline_url": None,
        "native_apk": False,
        "native_package_available": False,
        "physical_device_certified": False,
        "human_authority_final": True,
    }


'''
        source = replace_once(source, anchor, helper + anchor, name="store helper")
    else:
        # A previous partial adaptation may already have the helper; refuse to
        # silently rewrite a differently owned implementation.
        if '"browser_url": "/pay/bank"' not in source or '"browser_account_url": "/pay/bank/me"' not in source:
            raise ValueError("bank helper exists but browser fields differ; manual review required")
    if "_bank_information_entry()," not in source:
        source = replace_once(source, "        *PUBLIC_STORE_APPS,",
                              "        *PUBLIC_STORE_APPS,\n        _bank_information_entry(),",
                              name="catalogue entry")
    if '"browser_url": "/pay/bank"' not in source:
        raise ValueError("browser entry not found")
    return source


def apply_store_html(source: str) -> str:
    if 'href="{{ app.browser_url }}"' not in source:
        original = '      {% if app.open_url %}<a class="open-link" href="{{ app.open_url }}">Open {{ app.name }}</a>{% endif %}'
        replacement = '''      {% if app.browser_url %}<a class="open-link" href="{{ app.browser_url }}">Open in Browser</a>{% endif %}
      {% if app.browser_account_url %}<a class="open-link" href="{{ app.browser_account_url }}">My SIKA Account · Sign in</a>{% endif %}
      {% if app.open_url and not app.browser_url %}<a class="open-link" href="{{ app.open_url }}">Open {{ app.name }}</a>{% endif %}'''
        source = replace_once(source, original, replacement, name="store browser actions")
    if "Browser access requires no installation." not in source:
        source = replace_once(source, '    {% if app.app_id == "oap.arena" %}',
            '''    {% if app.app_id == "oap.usa_royalty_bank" %}
      <p class="truth">Browser access requires no installation. My SIKA Account is private and requires sign-in. Banking and payments remain evidence-gated.</p>
    {% endif %}
    {% if app.app_id == "oap.arena" %}''', name="store banking boundary")
    return source


def apply_detail_html(source: str) -> str:
    if 'href="/pay/bank/me"' not in source:
        source = replace_once(source, '<p><a style="color:#f7e1aa" href="/">OAP World</a></p>',
            '<p><a style="color:#f7e1aa" href="/pay/bank">Open in Browser</a> · <a style="color:#f7e1aa" href="/pay/bank/me">My SIKA Account (sign-in required)</a></p><p><a style="color:#f7e1aa" href="/">OAP World</a></p>', name="bank information links")
    return source


def apply_bank_html(source: str) -> str:
    if "{% set oap_install_script = false %}" not in source:
        source = replace_once(source, "{% set oap_app_name = 'OAP Bank' %}",
                              "{% set oap_install_script = false %}\n{% set oap_app_name = 'OAP Bank' %}",
                              name="no premature bank installer")
    if 'data-oap-install hidden' in source:
        original = '<div class="install-row">\n<button class="pill" type="button" data-oap-install hidden>Install OAP Bank</button>\n<div class="meta" data-oap-install-status role="status">Checking install support</div>\n</div>'
        replacement = '<div class="install-row">\n<a class="pill" href="/pay/bank/me">Open My SIKA Account</a>\n<div class="meta">Browser access available · Standalone installation not certified</div>\n</div>'
        source = replace_once(source, original, replacement, name="bank browser-only installer")
    if 'href="/pay/bank/me">My SIKA Account</a>' not in source:
        original = '<header class="top"><div class="brand">👑 OAP BANK</div><a class="pill" href="/pay">OAP Pay</a></header>'
        replacement = '<header class="top"><div class="brand">👑 OAP BANK</div><div style="display:flex;gap:8px;flex-wrap:wrap"><a class="pill" href="/pay/bank/me">My SIKA Account</a><a class="pill" href="/store">OAP Store</a><a class="pill" href="/pay">OAP Pay</a></div></header>'
        source = replace_once(source, original, replacement, name="bank header")
    if '<a class="nav" href="/pay/bank/accounts"><strong>▤</strong>Accounts</a>' in source:
        source = replace_once(source,
            '<a class="nav" href="/pay/bank/accounts"><strong>▤</strong>Accounts</a>',
            '<a class="nav" href="/pay/bank/me"><strong>▤</strong>My Account</a>',
            name="bank tab")
    return source


TRANSFORMS = {"store": apply_store, "store_html": apply_store_html,
              "detail_html": apply_detail_html, "bank_html": apply_bank_html}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write prepared changes after full validation")
    args = parser.parse_args()
    root = Path.cwd()
    transformed = {}
    try:
        for relative, transform in FILES.items():
            path = root / relative
            if not path.is_file():
                raise ValueError(f"missing required file: {relative}")
            current = path.read_text(encoding="utf-8")
            result = TRANSFORMS[transform](current)
            transformed[path] = (current, result)
        compile(transformed[root / "mission_control/oap_store.py"][1],
                "mission_control/oap_store.py", "exec")
    except (OSError, UnicodeError, ValueError, SyntaxError) as exc:
        print(f"STOP (no files modified): {exc}")
        return 2

    changed = [(p, new) for p, (old, new) in transformed.items() if old != new]
    print(f"SIKA browser integration: {len(changed)} file(s) need updating.")
    if not args.apply:
        print("Dry-run only; to apply use --apply. No server restart performed.")
        return 0
    backup_folder = root / ".sika-5052-backups" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    written = []
    try:
        if changed:
            backup_folder.mkdir(parents=True, exist_ok=False)
            for path, _ in changed:
                relative = path.relative_to(root)
                backup = backup_folder / relative
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, backup)
            for path, new in changed:
                # Write a temporary sibling and replace the target atomically.
                temp = path.with_name(path.name + ".sika-write-tmp")
                try:
                    temp.write_text(new, encoding="utf-8")
                    temp.replace(path)
                    written.append(path)
                finally:
                    temp.unlink(missing_ok=True)
    except OSError as exc:
        rollback_failed = []
        for path in reversed(written):
            try:
                shutil.copy2(backup_folder / path.relative_to(root), path)
            except OSError:
                rollback_failed.append(str(path))
        print(f"STOP: failed to write: {exc}. Backups: {backup_folder}")
        print("Rollback: " + ("FAILED for " + ", ".join(rollback_failed) if rollback_failed else "restored written files"))
        return 3
    print(f"Applied {len(changed)} file(s). Backups: {backup_folder if changed else 'none needed'}")
    print("Not deployed. No Arena, Oware, account balances, payment or server state touched.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
