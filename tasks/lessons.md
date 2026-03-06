# Lessons Learned

- When presenting after-tax backtest metrics, do not apply tax directly to equity curve deltas.
  Always compute tax from realized gains at transaction level (sell events), aggregate by tax year,
  then apply deduction/rate. Add a tax ledger output to make assumptions auditable.
- 사용자가 기준 엔진(원본 코드)을 제공했을 때는, 명시적 승인 없이 대체 구현으로 실행하지 않는다.
  먼저 원본 코드 그대로 재현 실행을 하고, 대체/개선 엔진은 분리 실험으로 제안한다.
- 사용자가 스트레스 테스트 구간을 특정(예: 2011년 이전)하면, 임의 구간 대체 없이 해당 구간을 반드시 포함해 보고한다.
  보고 전에 요청 구간 포함 여부를 체크리스트로 검증한다.
- 사용자가 알림 UI 샘플(이미지/스크린샷)을 제공하면, 섹션/문구/핵심 필드명을 샘플에 맞춰 우선 정렬하고 구현한다.
  "정보는 맞지만 형태가 다른" 상태로 완료 처리하지 않는다.
- 사용자가 "제가 해야 할 일 최소화"를 요청하면, 자동화 경로를 우선 제안하고
  사용자가 직접 해야 하는 항목을 1~2개 수준으로 축소해 명확히 분리 전달한다.
- 알림 UX 피드백이 오면 "읽기 좋은 문장"보다 "계기판형(수치+임계값)"을 우선한다.
  특히 액션 유무에 따라 템플릿 길이를 분리(무액션=짧게, 액션=상세)해야 실전 가독성이 높다.
