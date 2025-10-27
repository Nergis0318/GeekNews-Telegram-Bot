FROM ghcr.io/astral-sh/uv:alpine

WORKDIR /app

COPY . .

RUN apk update --no-cache && apk upgrade --no-cache

RUN uv sync --frozen --no-cache

EXPOSE 2001

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONHASHSEED=random

ENTRYPOINT ["uv", "run", "python3", "bot.py"]