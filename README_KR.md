# Limbus Company - 일본어 번역 교정 프로젝트

본 프로젝트는 『Limbus Company』의 공식 일본어 번역본에 포함된 오타 및 일부 오역을 교정하고, 그 수정 내역을 보고서 형식으로 제공하는 것을 목적으로 합니다.

- 교정 작업은 [ParaTranz](https://paratranz.cn/projects/14166)에서 진행되며, 해당 작업을 바탕으로 보고서가 생성됩니다.
- 부가적으로, 게임의 **사용자 지정 언어 기능**을 활용한 Mod도 배포하고 있습니다. 이는 프로젝트 참가자가 수정 내용을 게임 내에서 직접 확인할 수 있도록 하기 위한 것입니다.

## 📄 결과물

- `report_general.csv`  
  교정 보고서

- `report_storydata.csv`  
  교정 보고서 (스토리 관련)

- `Localize_Fixed/jp_fixed/`  
  교정이 반영된 일본어 번역 파일 (JP_*.json, 파일 구조는 Localize/jp/와 동일)

- `Localize_Fixed/jp_mod/`  
  위의 일본어 번역 파일을 기반으로 제작된 사용자 지정 언어 Mod

## 🛠 기타 구성 요소

- `Localize/kr/, Localize/en/, Localize/jp/`  
  공식 언어 파일 백업

- `paratranz/`  
  ParaTranz에서 다운로드한 번역 파일 백업

- `Utilities/Importer`  
  보고서 자동 생성 도구 (Localize/*, paratranz/* 파일 사용)

- `Utilities/`  
  프로젝트 관리 및 교정을 위한 Python 프로그램 모음

---

## 📝 보고서 분류

생성된 보고서 (`report_general.csv` / `report_storydata.csv`)에서는 다음과 같은 범주로 수정 내용을 분류합니다.

### ✅ 오타
일본어 번역에서 명백한 표기 오류. 아래와 같은 사례가 해당됩니다.

- 탈자
- 오자 (불필요한 문자)
- 오변환, 타이포
- 문단 누락
- 동음이의어 한자의 오용
- 숫자/키워드의 오타
- 표기 일관성 문제
- 기타 명확한 표기 오류

### ❓ 오역 의심
원문의 의미와 다르거나, 원문의 의도가 적절히 반영되지 않은 것으로 보이는 일본어 번역.

### 💬 표현 개선
일본어 표현이 어색하거나 장황하거나 거친 경우, 보다 자연스럽고 명확하게 조정합니다. 아래와 같은 사례가 해당됩니다.

- 전체적인 조정을 요하는 조사(てにをは) 및 문장 구조 오류
- 관용구 오용
- 중복 표현의 간소화
- 일본어로 의미를 파악하기 어렵게 번역된 경우
- 난해한 한자나 관용구에 대해 이해를 돕기 위한 후리가나 추가

##### "오타" 항목에는 반드시 수정안이 포함되며, 그 외의 범주는 문제 지적에만 그치고 수정안이 없는 경우도 있습니다.

---

### 📚 라이선스

본 저장소에 포함된 번역 교정 보고서 및 관련 프로그램은 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 라이선스 하에 공개됩니다.

본 저장소는 『Limbus Company』의 공식 번역 언어 파일을 기반으로 구성되었으며, 그에 포함된 원문 및 번역문 등의 저작권 및 기타 지적 재산권은 Project Moon에 귀속됩니다.

이 프로젝트는 비공식 프로젝트로, Project Moon이 보증하거나 관여하는 바는 없습니다. 본 저장소에 포함된 수정 제안 및 파생 데이터는 공식 번역의 품질 향상을 목적으로 하며, Project Moon이 참고용으로 활용할 수 있도록 하기 위한 것입니다.

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
