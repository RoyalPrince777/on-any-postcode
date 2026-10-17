"""Provider-loss readiness contract for OAP/SMI.

This module does not fail over infrastructure or mutate external providers.
It evaluates supplied evidence for whether OAP can survive loss of GitHub,
Render, or both without granting deployment, publication, or execution authority.
"""
from __future__ import annotations

import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path

_REQUIRED_CHECKS: tuple[str, ...] = (
    "local_git_history_available",
    "independent_repo_mirror_available",
    "release_manifest_preserved",
    "source_integrity_hashes_preserved",
    "provider_neutral_build_definition",
    "provider_neutral_start_command",
    "environment_inventory_preserved",
    "secrets_not_embedded_in_backup",
    "database_provider_separated",
    "database_backup_available",
    "database_restore_readback_proven",
    "object_storage_recovery_defined",
    "dns_recovery_defined",
    "health_check_provider_neutral",
    "rollback_artifact_preserved",
    "fresh_machine_restore_documented",
    "fresh_machine_restore_tested",
    "home_node_recovery_available",
    "alternate_host_path_defined",
    "audit_receipts_preserved",
    "human_authority_required",
)

_PROVIDER_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "github": (
        "local_git_history_available",
        "independent_repo_mirror_available",
        "release_manifest_preserved",
        "source_integrity_hashes_preserved",
    ),
    "render": (
        "provider_neutral_build_definition",
        "provider_neutral_start_command",
        "environment_inventory_preserved",
        "health_check_provider_neutral",
        "rollback_artifact_preserved",
        "alternate_host_path_defined",
    ),
    "github_and_render": _REQUIRED_CHECKS,
}

_REPOSITORY_ARTIFACTS: dict[str, tuple[str, ...]] = {
    "runtime_build": ("Dockerfile.runtime", "requirements.txt"),
    "home_node_posix": (
        "scripts/home_node_run.sh",
        "scripts/oap_home_node_supervisor.py",
        "scripts/oap_home_node_status.py",
    ),
    "home_node_termux": (
        "scripts/termux_home_node_run.sh",
        "scripts/termux_home_node_setup.sh",
        "scripts/termux_home_node_status.sh",
    ),
    "home_node_windows": ("scripts/home_node_run.ps1",),
    "home_node_contract": ("docs/HOME_NODE.md",),
    "host_core_contract": ("docs/OAP_HOST_CORE.md",),
    "release_control": (
        "deploy/oap-release-control-plane.json",
        "deploy/render-core-release.json",
        "deploy/render-image-release.json",
    ),
}


def required_checks() -> tuple[str, ...]:
    """Return the canonical 21-check provider-loss gate."""
    return _REQUIRED_CHECKS


def _run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    git = shutil.which("git")
    if not git:
        raise RuntimeError("git_executable_unavailable")
    return subprocess.run(
        [git, *args],
        cwd=repo,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )



def inspect_local_mirror(
    mirror_root: str | Path,
    *,
    expected_head: str,
) -> dict[str, object]:
    """Inspect a second local Git repository as a recovery mirror candidate.

    A separate repository path can prove clone/readback mechanics, but it does
    not by itself prove off-device, off-provider, or geographically independent
    storage.
    """
    mirror = Path(mirror_root)
    if not isinstance(expected_head, str) or len(expected_head) != 40:
        raise ValueError("expected_head_sha_required")
    if not mirror.is_dir():
        return {
            "mirror_present": False,
            "git_repository": False,
            "head_matches_expected": False,
            "object_integrity_ok": False,
            "independent_storage_proven": False,
            "network_access_used": False,
        }

    inside = _run_git(mirror, "rev-parse", "--git-dir")
    if inside.returncode != 0:
        return {
            "mirror_present": True,
            "git_repository": False,
            "head_matches_expected": False,
            "object_integrity_ok": False,
            "independent_storage_proven": False,
            "network_access_used": False,
        }

    head = _run_git(mirror, "rev-parse", "--verify", "HEAD")
    fsck = _run_git(mirror, "fsck", "--no-dangling", "--no-reflogs")
    head_sha = head.stdout.strip() if head.returncode == 0 else None

    return {
        "mirror_present": True,
        "git_repository": True,
        "head_sha": head_sha,
        "head_matches_expected": head_sha == expected_head,
        "object_integrity_ok": fsck.returncode == 0,
        "independent_storage_proven": False,
        "network_access_used": False,
    }


def verify_clean_clone_from_local_mirror(
    mirror_root: str | Path,
    clone_root: str | Path,
    *,
    expected_head: str,
) -> dict[str, object]:
    """Clone from a local mirror into an empty scratch path and verify readback.

    This is a bounded recovery drill. It proves that the supplied mirror can
    reproduce the expected Git HEAD in a clean clone. It does not prove the
    mirror is hosted independently from GitHub or on separate physical media.
    """
    mirror = Path(mirror_root)
    clone = Path(clone_root)
    if clone.exists():
        raise ValueError("clone_target_must_not_exist")
    mirror_status = inspect_local_mirror(mirror, expected_head=expected_head)
    if not (
        mirror_status["git_repository"]
        and mirror_status["head_matches_expected"]
        and mirror_status["object_integrity_ok"]
    ):
        return {
            "clone_attempted": False,
            "clone_succeeded": False,
            "head_matches_expected": False,
            "object_integrity_ok": False,
            "independent_storage_proven": False,
            "network_access_used": False,
            "mutation_scope": "none",
        }

    git = shutil.which("git")
    if not git:
        raise RuntimeError("git_executable_unavailable")
    result = subprocess.run(
        [git, "clone", "--no-hardlinks", str(mirror), str(clone)],
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    if result.returncode != 0:
        return {
            "clone_attempted": True,
            "clone_succeeded": False,
            "head_matches_expected": False,
            "object_integrity_ok": False,
            "independent_storage_proven": False,
            "network_access_used": False,
            "mutation_scope": "scratch_clone_only",
        }

    head = _run_git(clone, "rev-parse", "--verify", "HEAD")
    fsck = _run_git(clone, "fsck", "--no-dangling", "--no-reflogs")
    head_sha = head.stdout.strip() if head.returncode == 0 else None
    return {
        "clone_attempted": True,
        "clone_succeeded": True,
        "head_sha": head_sha,
        "head_matches_expected": head_sha == expected_head,
        "object_integrity_ok": fsck.returncode == 0,
        "independent_storage_proven": False,
        "network_access_used": False,
        "mutation_scope": "scratch_clone_only",
    }


def inspect_local_git_history(root: str | Path) -> dict[str, object]:
    """Perform a read-only local Git integrity inspection.

    This proves only the inspected local repository state. It does not prove an
    independent mirror, remote availability, backup durability, or recovery.
    """
    repo = Path(root)
    if not repo.is_dir():
        return {
            "repository_present": False,
            "git_repository": False,
            "head_sha": None,
            "shallow": None,
            "object_integrity_ok": False,
            "local_git_history_available": False,
            "independent_repo_mirror_proven": False,
            "network_access_used": False,
            "mutation_performed": False,
        }

    inside = _run_git(repo, "rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return {
            "repository_present": True,
            "git_repository": False,
            "head_sha": None,
            "shallow": None,
            "object_integrity_ok": False,
            "local_git_history_available": False,
            "independent_repo_mirror_proven": False,
            "network_access_used": False,
            "mutation_performed": False,
        }

    head = _run_git(repo, "rev-parse", "--verify", "HEAD")
    shallow = _run_git(repo, "rev-parse", "--is-shallow-repository")
    fsck = _run_git(repo, "fsck", "--no-dangling", "--no-reflogs")

    head_sha = head.stdout.strip() if head.returncode == 0 else None
    shallow_value = shallow.stdout.strip() if shallow.returncode == 0 else None
    object_integrity_ok = fsck.returncode == 0
    full_history = shallow_value == "false"
    available = bool(head_sha) and full_history and object_integrity_ok

    return {
        "repository_present": True,
        "git_repository": True,
        "head_sha": head_sha,
        "shallow": shallow_value == "true" if shallow_value in ("true", "false") else None,
        "object_integrity_ok": object_integrity_ok,
        "local_git_history_available": available,
        "independent_repo_mirror_proven": False,
        "network_access_used": False,
        "mutation_performed": False,
    }


def repository_artifact_snapshot(root: str | Path) -> dict[str, object]:
    """Report recovery-related repository artifacts without promoting them to proof.

    File presence is useful inventory evidence, but it cannot prove that a mirror,
    restore, alternate host, DNS switch, or live failover has actually worked.
    """
    repo = Path(root)
    groups: dict[str, dict[str, object]] = {}
    for name, paths in _REPOSITORY_ARTIFACTS.items():
        present = tuple(path for path in paths if (repo / path).is_file())
        missing = tuple(path for path in paths if not (repo / path).is_file())
        groups[name] = {
            "required_paths": paths,
            "present_paths": present,
            "missing_paths": missing,
            "complete": not missing,
        }

    return {
        "repository_root_exists": repo.is_dir(),
        "artifact_groups": groups,
        "artifact_inventory_only": True,
        "counts_as_provider_independence_proof": False,
        "automatic_failover_authorised": False,
        "deployment_authorised": False,
        "human_authority_final": True,
    }


def assess_provider_loss(
    evidence: Mapping[str, object],
    *,
    scenario: str = "github_and_render",
) -> dict[str, object]:
    """Evaluate supplied evidence and fail closed when proof is incomplete.

    Evidence values count only when they are literally True. Names, URLs,
    credentials, provider reachability, and architectural intent are not proof.
    """
    if scenario not in _PROVIDER_REQUIREMENTS:
        raise ValueError("unsupported_provider_loss_scenario")
    if not isinstance(evidence, Mapping):
        raise TypeError("evidence_mapping_required")

    required = _PROVIDER_REQUIREMENTS[scenario]
    passed = tuple(name for name in required if evidence.get(name) is True)
    missing = tuple(name for name in required if evidence.get(name) is not True)

    full_gate_passed = not missing
    dual_provider_survival_proven = scenario == "github_and_render" and full_gate_passed

    return {
        "scenario": scenario,
        "required_checks": required,
        "passed_checks": passed,
        "missing_checks": missing,
        "passed_count": len(passed),
        "required_count": len(required),
        "evidence_percent": round((len(passed) / len(required)) * 100, 1),
        "provider_independence_proven": full_gate_passed,
        "dual_provider_survival_proven": dual_provider_survival_proven,
        "github_is_replaceable_connector": full_gate_passed
        if scenario in ("github", "github_and_render")
        else None,
        "render_is_replaceable_connector": full_gate_passed
        if scenario in ("render", "github_and_render")
        else None,
        "automatic_failover_authorised": False,
        "deployment_authorised": False,
        "secret_recovery_proven": False,
        "database_restore_proven": evidence.get("database_restore_readback_proven") is True,
        "human_authority_final": True,
        "status": "CERTIFIED_EVIDENCE_SET" if full_gate_passed else "BUILDING",
    }
