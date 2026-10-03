FROM hasanara-ml-rocm:recollect-qualified
COPY app /app/app
COPY worker /app/worker
COPY pyproject.toml /app/pyproject.toml
COPY kvant-worker.py /app/kvant-worker.py
LABEL tv.subcult.worker.source="81b0d05" \
      tv.subcult.worker.runtime="20dea0673a68819aeacd269363b3e5ce232877f7d7e7598e6c028270a0bcb434"
ENV PYTHONDONTWRITEBYTECODE=1
RUN python3 -m compileall -q /app/app /app/worker
RUN mkdir -p /shared && test ! -e /data && ln -s /shared/data /data
CMD ["python3", "/app/kvant-worker.py"]
