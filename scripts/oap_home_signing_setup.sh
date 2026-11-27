#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

umask 077

KEY_DIR="${HOME}/oap-private"
KEYSTORE="${KEY_DIR}/oap-home-v2.jks"
ALIAS="oap-home-v2"
CERT_FILE="${KEY_DIR}/oap-home-cert-sha256.txt"
B64_FILE="${KEY_DIR}/oap-home-keystore.b64"

mkdir -p "${KEY_DIR}"
chmod 700 "${KEY_DIR}"

if ! command -v keytool >/dev/null 2>&1; then
  echo "keytool_not_found"
  exit 1
fi
if ! command -v base64 >/dev/null 2>&1; then
  echo "base64_not_found"
  exit 1
fi
if [[ -e "${KEYSTORE}" ]]; then
  echo "refusing_to_overwrite_existing_oap_home_identity"
  echo "${KEYSTORE}"
  exit 1
fi

printf 'Choose OAP Home keystore password: '
read -r -s STOREPASS
printf '\nConfirm keystore password: '
read -r -s STOREPASS2
printf '\n'
if [[ -z "${STOREPASS}" || "${STOREPASS}" != "${STOREPASS2}" ]]; then
  echo "password_confirmation_failed"
  exit 1
fi
if (( ${#STOREPASS} < 12 )); then
  echo "password_too_short_minimum_12"
  exit 1
fi

printf 'Choose OAP Home key password: '
read -r -s KEYPASS
printf '\nConfirm key password: '
read -r -s KEYPASS2
printf '\n'
if [[ -z "${KEYPASS}" || "${KEYPASS}" != "${KEYPASS2}" ]]; then
  echo "key_password_confirmation_failed"
  exit 1
fi
if (( ${#KEYPASS} < 12 )); then
  echo "key_password_too_short_minimum_12"
  exit 1
fi

keytool -genkeypair \
  -alias "${ALIAS}" \
  -keyalg RSA \
  -keysize 4096 \
  -validity 9125 \
  -keystore "${KEYSTORE}" \
  -storetype PKCS12 \
  -storepass "${STOREPASS}" \
  -keypass "${KEYPASS}" \
  -dname "CN=ON ANY POSTCODE LTD, OU=OAP Home, O=ON ANY POSTCODE LTD, C=GB"

CERT=$(
  keytool -list -v \
    -keystore "${KEYSTORE}" \
    -storepass "${STOREPASS}" \
    -alias "${ALIAS}" 2>/dev/null \
  | sed -n 's/^[[:space:]]*SHA256: //p' \
  | head -n1 \
  | tr -d ':[:space:]' \
  | tr '[:upper:]' '[:lower:]'
)

if [[ ! "${CERT}" =~ ^[0-9a-f]{64}$ ]]; then
  echo "certificate_fingerprint_failed"
  exit 1
fi

base64 < "${KEYSTORE}" | tr -d '\n' > "${B64_FILE}"
printf '%s\n' "${CERT}" > "${CERT_FILE}"
chmod 600 "${KEYSTORE}" "${B64_FILE}" "${CERT_FILE}"

unset STOREPASS STOREPASS2 KEYPASS KEYPASS2

echo "OAP_HOME_SIGNING_IDENTITY_CREATED"
echo "keystore=${KEYSTORE}"
echo "alias=${ALIAS}"
echo "certificate_sha256=${CERT}"
echo "keystore_base64_file=${B64_FILE}"
echo "github_secret_names=OAP_HOME_KEYSTORE_B64,OAP_HOME_KEYSTORE_PASSWORD,OAP_HOME_KEY_ALIAS,OAP_HOME_KEY_PASSWORD"
echo "github_variable_name=OAP_HOME_CERT_SHA256"
echo "PRIVATE_KEY_NOT_COMMITTED"
