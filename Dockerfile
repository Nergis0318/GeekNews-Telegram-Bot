FROM ghcr.io/astral-sh/uv:alpine

WORKDIR /app

COPY . .

RUN apk update --no-cache && apk upgrade --no-cache && apk add --no-cache build-base rust cargo

RUN uv sync --frozen --no-cache

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONHASHSEED=random

ENTRYPOINT ["uv", "run", "python3", "bot.py"]
