# Hands-on session 1 — 사전학습

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/kwongibaek/MS49900-AI4M/blob/main/Hand-on-session1/01_Preclass_Python_Pandas_Pymatgen.ipynb)

기본 학습 약 31분, MP 선택 예제 포함 약 34분입니다. 처음 설치하거나 서버 응답을 기다리는 시간은 별도로 걸릴 수 있습니다.

1. 위 버튼으로 Colab에서 노트북을 엽니다.
2. 첫 셀에서 `numpy`, `pandas`, `pymatgen`, `requests`를 설치합니다.
3. 둘째 셀에서 수업 저장소를 clone하고 `Hand-on-session1/Data/`를 읽습니다.
4. 위에서부터 차례로 실행합니다. 코드의 `##` 주석을 함께 읽어주세요.

설치 버전을 따로 고정하거나 Python 버전을 검사하지 않습니다. 설치 후 커널/런타임 재시작 안내가 나오면 재시작하고 처음부터 실행하세요.

로컬 Jupyter에서는 이 폴더 또는 저장소 최상위 폴더에서 열면 됩니다. 이미 받은 저장소는 다시 clone하지 않으며 자동으로 pull하거나 기존 파일을 덮어쓰지 않습니다. 현재 작업 폴더의 기존 `MS49900-AI4M` 다운로드 폴더가 불완전하면 Data 파일을 확인하라는 오류를 표시합니다.

## Data

| 파일 | 내용 |
|---|---|
| `steel_strength.csv` | 실험 강재 312행: 조성, 강도, 연신율 |
| `LiFePO4.cif` | pymatgen 공개 예제의 결정 구조 |
| `oqmd_li_fe_p_o_contains_sample.json` | 실제 OQMD 응답 사본 20행 |
| `sources.json` | 원본 주소, 설명, SHA-256 |

OQMD 셀은 기본적으로 실제 HTTP 요청을 보냅니다. 서버가 느리면 같은 검색 조건의 캐시로 전환하고 데이터 출처를 표시합니다. 캐시 전환은 정상적인 처리이므로 계속 진행하세요. MP 예제는 선택 사항이며 개인 API 키가 있어야 실행됩니다.

결과는 현재 작업 폴더의 `outputs/01_preclass/`에 저장됩니다. 개인 컴퓨터의 절대 경로, API 키, 실행 결과는 노트북에 포함하지 않았습니다.
