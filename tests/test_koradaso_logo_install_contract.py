from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts/koradaso_logo_install.sh").read_text()
PAGE = (ROOT / "templates/koradaso_internet.html").read_text()


def test_koradaso_asset_install_is_exact_and_fail_closed():
    assert 'dest="$repo/static/oap/koradaso_internet_logo.jpg"' in SCRIPT
    assert 'cmp -s "$src" "$tmp"' in SCRIPT
    assert 'cmp -s "$src" "$dest"' in SCRIPT
    assert "KORADASO_LOGO_CONFLICT" in SCRIPT
    assert "KORADASO_LOGO_NOT_JPEG" in SCRIPT
    assert 'mv -n -- "$tmp" "$dest"' in SCRIPT
    assert "curl " not in SCRIPT
    assert "git push" not in SCRIPT


def test_homepage_references_original_image_and_honest_controls():
    assert '/static/oap/koradaso_internet_logo.jpg' in PAGE
    assert 'href="/world"' in PAGE
    assert 'href="/settings"' in PAGE
    assert 'href="/mission/ollama"' in PAGE
    assert 'aria-disabled="true"' in PAGE
    assert "Personal bookmarks are not yet stored." in PAGE
