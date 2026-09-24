import re

with open("docs/01_governance/orchestrator-runtime-db-operations.md", "r") as f:
    content = f.read()

# Change the new heading from 5 to 6, and shift 5, 6, 7 down
content = content.replace("## 5. 백업 및 복구 기준", "## 6. 백업 및 복구 기준")
content = content.replace("## 6. 보안 및 기록 제한", "## 7. 보안 및 기록 제한")
content = content.replace("## 7. 미결 결정 사항 (사용자 확인 필요)", "## 8. 미결 결정 사항 (사용자 확인 필요)")

with open("docs/01_governance/orchestrator-runtime-db-operations.md", "w") as f:
    f.write(content)
