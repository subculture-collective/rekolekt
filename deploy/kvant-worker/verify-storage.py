"""Fail closed when the canonical media mount is absent."""

import os
from pathlib import Path
import subprocess

mount = Path('/home/onnwee/.local/state/hasanara-kvant/shared/data')
if not os.path.ismount(mount):
    raise SystemExit('HasanAra canonical media directory is not mounted')
if (mount / '.kvant-worker-storage-check').read_text().strip() != 'kvant worker storage qualification':
    raise SystemExit('HasanAra storage identity check failed')
result = subprocess.run(
    ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', 'almaz',
     'docker inspect hasanara-worker --format "{{.State.Running}}"'],
    capture_output=True, text=True, check=True,
)
if result.stdout.strip() != 'false':
    raise SystemExit('Almaz worker must be stopped before activating Kvant worker')
