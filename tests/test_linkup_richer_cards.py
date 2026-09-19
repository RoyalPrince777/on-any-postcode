from pathlib import Path


def test_certification_batch_labels_are_bounded_and_role_backed():
    source = Path("mission_control/certification.py").read_text(encoding="utf-8")

    assert "def labels_for_identities" in source
    assert "oap_identity_roles" in source
    assert "role_id=ANY(%s)" in source


def test_linkup_enriches_cards_with_proven_certifications():
    source = Path("app.py").read_text(encoding="utf-8")

    assert "certification.labels_for_identities" in source
    assert 'my_card["certifications"]' in source
    assert 'person["certifications"]' in source
    assert 'thread["certifications"]' in source
    assert 'thread["link_status"]' in source
    assert 'thread["link_kind"]' in source


def test_linkup_profile_surface_avoids_postcode_fallback_in_chat_header():
    page = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")

    assert "✓ {{ badge }}" in page
    assert "Purpose Link" in page
    assert "thread.postcode" not in page
    assert "person.certifications" in page
    assert "my_card.certifications" in page


def test_linkup_search_uses_safe_profile_context_not_exact_postcode():
    page = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")

    assert "thread.username" in page
    assert "thread.card_id" in page
    assert "thread.borough" in page
    assert "thread.country" in page
    assert 'data-search="{{ thread.display_name }} {{ thread.postcode' not in page
