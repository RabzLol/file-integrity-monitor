FROM python:3.14-slim

WORKDIR /app

RUN useradd --create-home --uid 10001 fimuser

COPY --chown=fimuser:fimuser monitor.py .

USER fimuser

ENTRYPOINT ["python", "monitor.py"]
