#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

REPO_URL="https://github.com/RoyalPrince777/on-any-postcode.git"
REPO_DIR="${OAP_HOME_REPO:-$HOME/on-any-postcode}"

printf '%s
' "OAP Personal Telecom setup"
printf '%s
' "Software install only. External licence/carrier/number/radio authority remains Founder responsibility."

pkg install -y python git

if [[ -d "$REPO_DIR/.git" ]]; then
  printf 'Using existing repository: %s
' "$REPO_DIR"
elif [[ -e "$REPO_DIR" ]]; then
  printf 'Refusing to overwrite non-repository path: %s
' "$REPO_DIR" >&2
  exit 2
else
  git clone --branch main --single-branch "$REPO_URL" "$REPO_DIR"
fi

cd "$REPO_DIR"

python -m mission_control.personal_telecom_install --yes
python -m mission_control.personal_telecom_install --yes --apply
python -m mission_control.personal_telecom_install --status

printf '%s
' ""
printf '%s
' "Installed OAP Personal Telecom control-plane state."
printf '%s
' "OAP Number remains first-party identity only until external gates are proven."
printf '%s
' ""
printf '%s
' "Optional authority references (opaque references only; never paste SIM keys or private credentials):"
printf '%s
' "  export OAP_CARRIER_PROFILE_AUTHORITY_REF='your-reference'"
printf '%s
' "  export OAP_CARRIER_ACTIVATION_AUTHORITY_REF='your-reference'"
printf '%s
' "  export OAP_PRIVATE_RADIO_AUTHORITY_REF='your-reference'"
printf '%s
' "  export OAP_PUBLIC_NUMBER_AUTHORITY_REF='your-reference'"
printf '%s
' ""
printf '%s
' "Re-run status:"
printf '  cd %q && python -m mission_control.personal_telecom_install --status
' "$REPO_DIR"
printf '%s
' "Rollback local install state:"
printf '  cd %q && python -m mission_control.personal_telecom_install --yes --apply --uninstall
' "$REPO_DIR"
