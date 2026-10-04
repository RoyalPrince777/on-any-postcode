#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

REPO_URL="https://github.com/RoyalPrince777/on-any-postcode.git"
REPO_DIR="${OAP_HOME_REPO:-$HOME/on-any-postcode}"
STATE_DIR="$HOME/.local/state/oap-personal-telecom"
BACKUP_PATCH="$STATE_DIR/pre-upgrade.patch"
STASH_CREATED=0

restore_local_changes() {
  if (( STASH_CREATED == 1 )); then
    printf '%s
' "Restoring local OAP edits..."
    if git stash apply stash@{0}; then
      git stash drop stash@{0} >/dev/null
      STASH_CREATED=0
      printf '%s
' "Local edits restored."
    else
      printf '%s
' "Automatic restore hit conflicts. Stash has been preserved." >&2
      printf 'Tracked-change backup: %s
' "$BACKUP_PATCH" >&2
      printf '%s
' "Resolve conflicts manually; do not reset or delete the stash." >&2
      return 1
    fi
  fi
}

trap 'status=$?; if (( STASH_CREATED == 1 )); then restore_local_changes || true; fi; exit $status' EXIT

printf '%s
' "OAP Personal Telecom full setup"
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
mkdir -p "$STATE_DIR"
chmod 700 "$STATE_DIR"

git fetch origin main

current_branch="$(git branch --show-current)"
if [[ "$current_branch" != "main" ]]; then
  printf 'Refusing install from branch %s; switch to main first.\n' "$current_branch" >&2
  exit 2
fi

if [[ -n "$(git status --porcelain)" ]]; then
  printf '%s
' "Local OAP edits detected; preserving them before upgrade."
  git diff --binary > "$BACKUP_PATCH"
  chmod 600 "$BACKUP_PATCH"
  git stash push -u -m "OAP automatic backup before personal telecom full upgrade"
  STASH_CREATED=1
fi

git pull --ff-only origin main

printf 'Installing from revision: %s
' "$(git rev-parse HEAD)"

python -m mission_control.personal_telecom_install --yes
python -m mission_control.personal_telecom_install --yes --apply
python -m mission_control.personal_telecom_install --verify

if (( STASH_CREATED == 1 )); then
  restore_local_changes
fi

trap - EXIT

printf '%s
' ""
printf '%s
' "OAP Personal Telecom install verified."
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
' "Verify again:"
printf '  cd %q && python -m mission_control.personal_telecom_install --verify
' "$REPO_DIR"
printf '%s
' "Rollback local install state:"
printf '  cd %q && python -m mission_control.personal_telecom_install --yes --apply --uninstall
' "$REPO_DIR"
