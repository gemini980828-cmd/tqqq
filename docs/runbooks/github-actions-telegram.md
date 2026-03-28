# GitHub Actions 기반 일일 텔레그램 알림 운영

## 개요
로컬 PC cron 대신 GitHub Actions에서 매일 자동 실행해 텔레그램으로 신호를 전송한다.

워크플로 파일: `.github/workflows/daily-telegram.yml`

## 실행 흐름
1. `prepare_user_csv.py`로 최신 데이터 생성
2. `run_final_core_strategy_signal.py`로 `phase2-best + soft_overheat_buffer(129/123/0.90)` 최종 신호 산출
3. `run_manager_summaries.py`로 manager summary cache 갱신
4. `export_dashboard_snapshot.py`로 Home/Manager 대시보드 snapshot 갱신
5. `run_daily_telegram_alert.py`로 텔레그램 발송

## 스케줄
- UTC 기준: `30 22 * * 1-5`
- 목적: 미국 장 마감 이후 여유 시간에 1회 실행(DST/표준시 공통)

## 필수 사용자 작업 (딱 2개)
GitHub 저장소 Settings → Secrets and variables → Actions → New repository secret
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## 수동 테스트
GitHub > Actions > `Daily Telegram Signal Alert` > `Run workflow`

## 장애 확인
- 실행 로그: Actions Job 로그 확인
- 산출물: `daily-telegram-artifacts` 아티팩트 확인
- 실패 원인 우선순위:
  1. Telegram secrets 누락
  2. yfinance 네트워크/데이터 응답 이슈
  3. 스크립트 예외

## 참고
- 최종 운영 신호 파일은 `reports/signals_core_strategy_final.csv`이다.
- 이 파일은 `phase2-best` 코어 위에 `soft_overheat_buffer(129/123/0.90)`를 적용해 생성된다.
- `reports/daily_telegram_alert_state_gha.json`은 러너가 매번 초기화되므로 장기 멱등 상태 저장 용도로는 쓰지 않는다.
- 동일 날짜 수동 재실행 시 메시지가 중복 발송될 수 있다.
- 총괄 Orchestrator 대화는 GitHub Actions에서 자동 호출하지 않는다. Home UI에서 **사용자가 명시적으로 질문했을 때만** cache-first 답변을 사용한다.
- backend helper를 통해 orchestrator를 호출하는 환경에서는 `reports/orchestrator_audit.jsonl`에 prompt/result metadata가 기록될 수 있다. 이 로그는 비용/디버깅 용도이며 권위 데이터 소스는 아니다.
