FROM git.subcult.tv/subculture-collective/hasanara-api@sha256:92f0979ed99a81e65c88f3150e20e707a7154d32abda659066d9ce0ae2136db9
LABEL tv.subcult.availability.patch="7cde278" \
      tv.subcult.availability.base="sha256:92f0979ed99a81e65c88f3150e20e707a7154d32abda659066d9ce0ae2136db9"
COPY orchestrator.py /app/app/search/orchestrator.py
COPY health.py /app/app/routes/health.py
COPY segment_repository.py /app/app/search/segment_repository.py
RUN python -m compileall -q /app/app/search/orchestrator.py /app/app/routes/health.py
