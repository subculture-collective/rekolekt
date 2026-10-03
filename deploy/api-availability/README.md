# October 3 API availability repair

Almaz's API now runs a temporary incident image containing the external-index
freshness repair and indexed YouTube title lookups from core commit `7cde278`.
The source changes are under review in
[Rekolekt PR 48](https://git.subcult.tv/subculture-collective/rekolekt/pulls/48).

The image changes three Python modules from the deployed base, preserving all
dependencies and other application files. No schema, index, data, or queue
mutation is part of this repair.

- Base image: `sha256:92f0979ed99a81e65c88f3150e20e707a7154d32abda659066d9ce0ae2136db9`.
- Incident image: `sha256:7ad07c3ae78f03a42d0fb35a0214933f22e5c8bcd6072b924b698145cc12db6a`.
- Local Almaz tag: `hasanara-api:availability-7cde278`.
- Runtime receipt and build context: `~/.local/state/hasanara/availability-20261003/` on Almaz.

`Dockerfile` records the exact build recipe. Its context contains `orchestrator.py`,
`health.py`, and `segment_repository.py` copied from the core commit. The local
incident image has not been published as a registry release.

`apply.py` runs the existing production preflight, compares resolved Compose
configuration without printing its secrets, and refuses any change beyond the API
image. It recreates only `api` with `--no-deps --no-build --pull never`. The original
CUDA worker must remain stopped. Private before-state receipts are retained; the
script refuses to overwrite them or operate against an unexpected API image.

The October 3 application is complete. To roll back on Almaz:

```sh
rtk proxy python ~/.local/state/hasanara/availability-20261003/apply.py --rollback
```

The receipt directory contains `api.before.json`, the private Compose image
override, source modules, and running-container identities. Preserve these files
and any later changes before recovery. The rollback command uses the original
release configuration for only the API; it does not start the CUDA worker.

A normal full production deploy will revert this temporary API image unless a
published release containing PR 48 replaces it. It will also start Almaz's worker
under the current Compose topology. Preserve Kvant's ownership when preparing that
release; do not run a full Almaz deploy as an incident-image refresh.

Validation: 47 focused tests passed in the isolated Kvant launcher, including real
PostgreSQL tests for earliest title segments across multiple transcripts. Ruff and
the network-disabled incident-image compile check passed. Live read-only EXPLAIN
verified the existing caption time index and absence of a YouTube segment sequential
scan. Only the API container identity changed. The first scheduled Dozor check
after deployment passed; archive summary responded in approximately 0.3 seconds.
Common-word search returned 10 results in approximately 12 seconds after old reads
drained. The initial search during that drain exceeded 30 seconds. This is live
recovery evidence, with no claim of full-suite, hosted CI, or sustained-load proof.
