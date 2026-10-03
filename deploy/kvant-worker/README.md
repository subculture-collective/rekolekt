# Temporary HasanAra worker on Kvant

Activated October 3, 2026 after Almaz's GTX 1080 stopped responding. This moves
the ingestion/transcription worker. PostgreSQL, web/API, enrichment and archive
refreshers remain on Almaz. The API still has an independent database I/O problem.

The installed worker image is
`sha256:81d904dca7e2f9adc4e039be0591933aa10e0be41e7680f0a72aaef54104fd3b`.
It combines core source `81b0d05` with the previously qualified ROCm runtime
`sha256:20dea0673a68819aeacd269363b3e5ce232877f7d7e7598e6c028270a0bcb434`.
The Dockerfile's named local base must match that runtime before rebuilding.
Build context needs `app/`, `worker/`, and `pyproject.toml` from that exact core
revision, plus this Dockerfile and `kvant-worker.py`. The locally built image is
not a hosted or signed release artifact.

Kvant uses its RX 7900 XT with PyTorch Whisper, model `small`, forced GPU,
one concurrent job, four CPU cores and a 6 GiB memory limit. `/data` resolves to
the exact Almaz media directory through SSHFS. Mount the **parent** directory
`~/.local/state/hasanara-kvant/shared` at `/shared:rslave`; directly binding the
unprivileged FUSE mount fails Docker's root-side source-path checks. The container
runs as UID/GID 1000. No system FUSE permission change is needed.

The three user systemd units in this directory are installed on Kvant. The worker
requires the SSH database tunnel and storage mount, checks the mount identity and
that the Almaz worker is stopped, then attaches to the prepared Docker container.
Database and metrics listeners bind only to `127.0.0.1` on Kvant, ports 15438 and
8001. Host networking avoids exposing the tunnel through Docker bridge firewall
rules. Container restart policy is `no`; systemd owns startup ordering.

Private installation state is `~/.local/state/hasanara-kvant/`. `worker.env` is
mode 600 and contains the copied worker environment with the database connection
pointing through the SSH tunnel. Cache paths use `/cache`, not `/root/.cache`.
Do not commit this environment, cookie cache, or private transfer receipts.
The earlier cookie path did not name an existing Almaz file; yt-dlp now creates its
cookie cache at the writable Kvant path. All three channel discoveries passed.

Qualification passed: GPU arithmetic, a twelve-second real audio excerpt both
before deployment and inside the final running image, production configuration
validation, database `SELECT 1`, shared-file read/write with Almaz readback,
channel discovery and live database heartbeat. The eligible queue was empty;
no full VOD processing or reboot/reconnection soak is claimed. Existing job
eligibility, failures and approvals were preserved.

## Operation and rollback

Check `systemctl --user status hasanara-kvant-worker.service` and
`docker logs hasanara-kvant-worker`. The local metrics endpoint is
`http://127.0.0.1:8001/metrics`; database heartbeats use
`worker_id=hasanara-kvant-worker-1`.

Almaz's original `hasanara-worker` container was gracefully stopped with exit 0
and retained. **Do not run a full Almaz Compose deployment while this worker owns
ingestion:** the old Compose topology still includes the worker and can start it.
The original release guard requires that topology; it was not weakened during
this temporary migration.

To retire the Kvant worker, stop its user service and wait for its active job to
drain. The service permits ten minutes before forcibly stopping a job. Inspect
the active lease and current queue before changing ownership. Then disable its
service and the two helper services. Keep the local state, model cache and original
container for recovery. Start the Almaz worker only after a GPU compute and model
decode check passes there; an absent Kvant worker does not repair the GTX 1080.

Installed unit contents and the Docker create arguments are recorded in the
canonical Machinum incident report. This directory owns the non-secret service
definitions and launcher; the installed copies are deployment targets.
