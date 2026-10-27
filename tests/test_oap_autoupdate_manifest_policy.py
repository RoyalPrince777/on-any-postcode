"""Static source contract; no network calls or APK installation."""
from pathlib import Path

SOURCE = Path("android/oaphome/src/main/java/com/onanypostcode/oaphome/OapUpdateManifestPolicy.java")


def test_local_candidate_policy_not_an_updater():
    source = SOURCE.read_text(encoding="utf-8")
    for marker in (
        'OWNED_HOST = "www.onanypostcode.com"',
        '"https".equals(uri.getScheme())',
        'uri.getRawUserInfo() == null',
        'uri.getPort() == -1',
        'uri.getRawQuery() == null',
        'uri.getRawFragment() == null',
        'uri.getRawPath().startsWith("/oap-updates/apks/")',
        'uri.getRawPath().endsWith(".apk")',
        '!uri.getRawPath().contains("..")',
        'value.matches("[A-Fa-f0-9]{64}")',
        'version <= installedCode',
        'installedPackage.equals(pkg)',
        'obj.length() != 5',
        'MAX_MANIFEST_CHARS = 8192',
    ):
        assert marker in source
    for forbidden in ("PackageInstaller", "DownloadManager", "HttpURLConnection",
                      "startActivity(", "installPackage(", "setInstallerPackageName"):
        assert forbidden not in source
