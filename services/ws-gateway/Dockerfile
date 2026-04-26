FROM python:3.12-slim-bookworm AS test
WORKDIR /app
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends dumb-init \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
COPY src ./src
COPY tests ./tests
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir ".[dev]"
RUN pytest -q

FROM python:3.12-slim-bookworm AS runtime
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends dumb-init \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .
ENV PORT=8080
ENV HOST=0.0.0.0
EXPOSE 8080
USER nobody
ENTRYPOINT ["dumb-init", "--"]
CMD ["sh", "-c", "exec uvicorn ws_gateway.main:app --host \"${HOST}\" --port \"${PORT}\" --no-access-log"]
