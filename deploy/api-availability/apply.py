"""Apply the tested October 3 API repair without starting the CUDA worker.

Run on Almaz with --apply or --rollback. Retains the original Compose configuration
and private runtime receipt; never prints resolved environment values.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import time

BASE = "sha256:92f0979ed99a81e65c88f3150e20e707a7154d32abda659066d9ce0ae2136db9"
PATCH = "sha256:7ad07c3ae78f03a42d0fb35a0214933f22e5c8bcd6072b924b698145cc12db6a"


def inspect(name):
    return json.loads(subprocess.check_output(["docker", "inspect", name]))[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--apply", action="store_true")
    actions.add_argument("--rollback", action="store_true")
    rollback = parser.parse_args().rollback
    api = inspect("hasanara-api")
    if api["Image"] != (PATCH if rollback else BASE):
        raise RuntimeError("API image changed; inspect current ownership before proceeding")
    if inspect("hasanara-worker")["State"]["Running"]:
        raise RuntimeError("Almaz CUDA worker must remain stopped")
    if not rollback:
        labels = inspect(PATCH)["Config"]["Labels"]
        if labels.get("tv.subcult.availability.patch") != "7cde278":
            raise RuntimeError("Unexpected patch provenance")
    labels = api["Config"]["Labels"]
    root = Path(labels["com.docker.compose.project.working_dir"])
    files = labels["com.docker.compose.project.config_files"].split(",")
    files = [f for f in files if not f.endswith("api-availability.override.json")]
    env = {k: os.environ[k] for k in ("PATH", "HOME", "USER") if k in os.environ}
    env.update(HASANARA_ENV_FILE=".env.prod", TRANSCRIPT_DEPLOY_ROOT=str(root), TRANSCRIPT_CORE_DIR=str(root / "core"))
    subprocess.run([str(root / "bin/compose-prod"), "preflight"], cwd=root, env=env, check=True)
    command = ["docker", "compose", "--project-name", "hasanara", "--project-directory", str(root), "--env-file", ".env.prod"]
    for file in files:
        command += ["--file", file]
    receipt = Path.home() / ".local/state/hasanara/availability-20261003"
    receipt.mkdir(mode=0o700, parents=True, exist_ok=True)
    override = receipt / "api-availability.override.json"
    override.write_text(json.dumps({"services": {"api": {"image": PATCH}}}))
    override.chmod(0o600)
    base_config = json.loads(subprocess.check_output(command + ["config", "--format", "json"], cwd=root, env=env))
    patched = command + ["--file", str(override)]
    patch_config = json.loads(subprocess.check_output(patched + ["config", "--format", "json"], cwd=root, env=env))
    assert inspect(base_config["services"]["api"]["image"])["Id"] == BASE
    patch_config["services"]["api"]["image"] = base_config["services"]["api"]["image"]
    if patch_config != base_config:
        raise RuntimeError("Override must change only the API image")
    before = receipt / ("api.before-rollback.json" if rollback else "api.before.json")
    if before.exists():
        raise RuntimeError("Private receipt already exists; preserve prior execution evidence")
    before.write_text(json.dumps(api))
    before.chmod(0o600)
    target = command if rollback else patched
    subprocess.run(target + ["up", "-d", "--no-deps", "--no-build", "--pull", "never", "api"], cwd=root, env=env, check=True)
    for _ in range(60):
        current = inspect("hasanara-api")
        if current["State"].get("Health", {}).get("Status") == "healthy":
            assert current["Image"] == (BASE if rollback else PATCH)
            assert not inspect("hasanara-worker")["State"]["Running"]
            print("API healthy; expected immutable image verified; CUDA worker remains stopped")
            return
        time.sleep(1)
    raise RuntimeError("API health not established; inspect logs and use --rollback")


if __name__ == "__main__":
    main()
