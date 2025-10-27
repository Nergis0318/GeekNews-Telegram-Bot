# GeekNews-Telegram-Bot
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2FDevNergis%2FGeekNews-Telegram-Bot.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2FDevNergis%2FGeekNews-Telegram-Bot?ref=badge_shield)


RSS에서 GeekNews 기사를 가져와서 텔레그램으로 전송하는 봇입니다.

## 기능

- 📰 RSS 피드에서 새로운 기사를 자동으로 가져옵니다
- 💬 텔레그램으로 구독자에게 새 기사를 전송합니다
- ✅ `/start`, `/sub` 명령으로 구독 시작
- 🛑 `/stop`, `/unsub` 명령으로 구독 해제
- 🗄️ SQLite로 구독자 및 전송 기록 관리
- 🔄 5분마다 자동으로 새로운 기사 확인

## 설치

이 프로젝트는 UV 패키지 관리자를 사용합니다.

- [UV 설치 (아직 설치하지 않은 경우)](https://docs.astral.sh/uv/getting-started/installation/)

```bash
# 의존성 설치
uv sync
```

## 설정

1. `.env` 파일에 텔레그램 봇 토큰을 입력합니다
   - `.env.example` 파일을 참고하세요

## 파일 구조

```
.
├── bot.py             # 메인 봇 코드
├── pyproject.toml     # UV 프로젝트 설정
├── uv.lock            # 의존성 잠금 파일
├── .env.example       # 환경 설정 예시
├── bot.db             # SQLite 데이터베이스 (자동 생성)
└── README.md          # 이 파일
```

## 실행

### 방법 1: 직접 실행

```bash
uv run bot.py
```

또는:

```bash
.venv/bin/python bot.py
```

## 사용법

텔레그램에서 봇과 대화를 시작합니다:

- `/start` - GeekNews 구독 시작
- `/stop` - GeekNews 구독 해제

봇이 실행 중이면 5분마다 새로운 기사를 확인하고 구독자에게 전송합니다.

## 기술 스택

- Python
- python-telegram-bot
- feedparser
- SQLite3
- UV (패키지 관리자)

## 라이센스

- **GNU Affero General Public License v3.0**


## License
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2FDevNergis%2FGeekNews-Telegram-Bot.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2FDevNergis%2FGeekNews-Telegram-Bot?ref=badge_large)