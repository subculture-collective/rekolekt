"""Run the remote-storage worker with host-local metrics."""

from functools import partial

from prometheus_client import start_http_server

from worker import loop

loop.start_http_server = partial(start_http_server, addr="127.0.0.1")
loop.main()
