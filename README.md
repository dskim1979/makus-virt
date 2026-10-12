<h1 align="center">MOAVI</h1>

<p align="center">
  <strong>Proxmox VE · XCP-ng 멀티 클러스터 통합 관리 — 한국 운영 환경에 맞춘 오픈소스 에디션</strong>
</p>

<p align="center">
  <a href="https://github.com/dskim1979/makus-virt/releases">릴리스</a> •
  <a href="https://github.com/dskim1979/makus-virt/issues">문의·버그</a> •
  <a href="#-설치">설치</a> •
  <a href="#-기반-프로젝트와-라이선스">기반 프로젝트와 라이선스</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.3.0-blue" alt="Version"/>
  <img src="https://img.shields.io/badge/python-3.10+-green" alt="Python"/>
  <img src="https://img.shields.io/badge/license-AGPL--3.0-orange" alt="License"/>
  <img src="https://img.shields.io/badge/based%20on-PegaProx-lightgrey" alt="Based on PegaProx"/>
</p>

---

## 소개

**MOAVI(모아비)** 는 여러 Proxmox VE 클러스터와 XCP-ng 풀을 웹 브라우저 한 화면에서 모니터링·운영·관리하는 오픈소스 플랫폼입니다.
오픈소스 프로젝트 [PegaProx](https://github.com/PegaProx/project-pegaprox)(AGPL-3.0)를 바탕으로, **(주)매커스시스템즈(Makus Systems)** 가
한국 공공·기업 운영 환경에 맞게 기능을 더하고 한국어로 다듬어 유지보수합니다.

- 별도 에이전트 없이 Proxmox VE API(일부 기능은 노드 SSH)로 동작
- 인터넷이 없는 격리망에서도 동작 (화면에 필요한 라이브러리를 모두 내장)
- 소스 전체 공개 — AGPL-3.0

## MOAVI 가 더한 기능

| 기능 | 내용 |
|---|---|
| 📑 **한국형 보고서** | 공공기관 보고 양식 3종 — **가상화 인프라 운영 현황 보고**, **자원 사용 현황 및 증설 검토**, **가상서버 자원 현황 대장**. 보고 기간·대상 클러스터·작성 정보(기관·부서·작성자·보안 등급 표시)를 고르면 실시간 미리보기, **PDF·한글(HWPX)·워드(DOCX)·엑셀(XLSX)** 로 내려받기. 기간 중 CPU·메모리 사용률(평균·최대), 스토리지 사용률, 백업 결과, 하드웨어 이상 포함 → [문서](docs/korean-reports.md) |
| 🩺 **하드웨어(BMC) 상태 이력** | 5분마다 읽는 서버 하드웨어 상태(노드 안 ipmitool 우선, Redfish 보조)에서 이상 **발생·등급 상승·복구**를 기록 → 운영 현황 보고서에 보고 기간 중 하드웨어 이상과 복구 시각 표시 |
| 🎮 **GPU / vGPU 관리** | 클러스터 GPU 현황·사용률, GPU 통째 패스스루 또는 NVIDIA vGPU(mdev) 할당 |
| 💰 **원화(KRW) 비용 대시보드** | 국내 전기요금·장비 비용 기준으로 VM 별 월 비용 산정 |
| 🇰🇷 **한국어 화면** | 다국어 대신 한국어에 집중한 화면·문구 |
| 🎨 **화이트라벨** | 로고·파비콘·앱 이름을 배포 환경에 맞게 변경 |

## 주요 기능

### 멀티 클러스터 관리
- 여러 Proxmox VE 클러스터를 한 화면에서 — 실시간 CPU·메모리·스토리지 현황(SSE)
- 노드 간 실시간 이전(라이브 마이그레이션), 클러스터 간 부하 분산
- ESXi · Proxmox VE · XCP-ng 사이 VM 이전

### 가상머신·컨테이너
- 시작·정지·재시작, CPU·메모리·디스크·네트워크·EFI·Secure Boot 설정
- 스냅숏(공유 스토리지용 공간 절약 LVM 스냅숏 포함), ZFS 가 없는 클러스터용 스냅숏 복제
- 백업 일정·관리, 백업 복원 검증(실험 기능: 복원 → 부팅 → 상태 확인 → 정리)
- 브라우저 콘솔(noVNC · xterm.js, SPICE 파일 내려받기)
- 노드 간 자동 분산, 고가용성(HA) 자동 재시작, 함께/떨어뜨려 두기 규칙(Affinity)
- OCI 이미지로 만드는 앱 컨테이너, 여러 게스트 한 번에 처리(스냅숏·태그·마이그레이션), 마이그레이션 사전 점검

### XCP-ng (기술 미리보기)
- XCP-ng / Xen 풀 연결, 전원 동작, VNC 콘솔, 디스크·NIC 관리, 유지 보수 모드

### ESXi 이전
- ESXi 가져오기 마법사 — 실행 중 VM 의 최소 중단 이전 또는 중지 후 이전 (ESXi SSH 필요)

### 보안·접근 제어
- 역할 기반 권한(관리자·운영자·조회자 + 사용자 정의 역할), VM 단위 권한, 멀티 테넌트
- 2단계 인증(TOTP), WebAuthn / FIDO2 보안 키, LDAP / OIDC(AD, Entra ID, Keycloak 등)
- API 토큰, IP 허용·차단
- 데이터베이스 전체 암호화(SQLCipher, Linux x86_64), 민감 정보 필드 암호화
- 노드 패키지 취약점(CVE) 점검, CIS 기준 보안 점검·강화, 위변조 확인이 되는 감사 로그

### 자동화·모니터링
- 예약 작업(시작·정지·스냅숏·백업), 태그·VM 목록 기준 스냅숏 정책과 보존 정리
- 노드 순차 업데이트(VM 자동 대피)
- **MOAVI 자체 고가용성** — 최대 4대의 MOAVI 를 한 그룹으로(리더 1 + 대기), 리더 장애 시 관리자 확인 후 승격
- Proxmox VE 자동 설치(응답 파일 프로필·설치 진행 추적), 리소스 매핑(디렉터리·PCI·USB)
- 알림 규칙(CPU·메모리·디스크·온도·**하드웨어 상태**), 감사 로그 검색·CSV 내보내기
- 서버 하드웨어 상태(BMC) — 센서·전원공급장치·섀시·이벤트 로그(SEL), 클러스터 하드웨어 이상 요약
- SIEM 전송(Syslog, Splunk HEC, Elasticsearch, Loki, 웹훅), 내장 Syslog 서버
- Ceph 관리·RBD 미러링, ACME / Let's Encrypt 인증서 자동 갱신
- 구성 변경 감지(기준 대비 무단 변경 알림)

### 보고·분석
- **한국형 보고서** (위 표)
- 비용 대시보드(과금), 전력·탄소 추정, 자원 적정 크기·용량 예측(Insights)
- 네트워크 구성도(클러스터 → 노드 → 브리지·본드·SDN → VM)
- 규정 준수 현황판, CVE 보고

### 운영·배포
- Cloud-Init 템플릿 목록(Ubuntu·Debian·AlmaLinux·Rocky·Fedora·Alpine) 한 번에 배포
- 사이트 복구(DR) 계획과 통제된 장애 전환, 백업 SLA(RPO) 현황
- ZFS·클러스터 간 복제, VMware 이전(VirtIO 드라이버 사전 설치)

### 알림 채널·플러그인
- Slack · Discord · Microsoft Teams · ntfy · 웹훅, 브라우저 푸시, 설치형 웹 앱(PWA)
- 고객 셀프 서비스 포털, 공개 상태 페이지, 알림 플러그인, 플러그인 설정 편집

### 그 밖에
- 격리망(오프라인) 모드, 다크·라이트 등 테마, 트리형 사이드바 레이아웃
- Proxmox Backup Server 관리, Prometheus 지표(`/api/metrics`)

## 📋 요구 사항

- Python 3.10 이상, Linux 서버
- Proxmox VE 8.0 이상 또는 9.0 이상, 그리고/또는 XCP-ng 8.2 이상
- Chrome · Edge · Firefox · Safari 최신 버전
- 포트: **5000**(웹), 5001(VNC 콘솔), 5002(노드 셸)

## ⚡ 설치

> ⚠️ 원본 PegaProx 의 APT 저장소(`apt install pegaprox`)·Docker 이미지(`ghcr.io/pegaprox/pegaprox`)·설치 주소를 쓰면
> MOAVI 가 아니라 **원본 PegaProx** 가 설치됩니다. 아래 방법으로 설치하세요.

### 자동 설치 (권장)
```bash
curl -O https://raw.githubusercontent.com/dskim1979/makus-virt/main/deploy.sh
chmod +x deploy.sh
sudo ./deploy.sh
```
main 브랜치 최신 코드를 `/opt/PegaProx` 에 설치하고 서비스로 등록합니다.

### 소스에서 설치
```bash
git clone https://github.com/dskim1979/makus-virt.git
cd makus-virt
pip install -r requirements.txt
python3 pegaprox_multi_cluster.py
```
화면 소스(`web/src/`)를 고쳤다면 `bash web/Dev/build.sh` 로 `web/index.html` 을 다시 만듭니다 (Node.js 16 이상).

### Docker (직접 빌드)
```bash
git clone https://github.com/dskim1979/makus-virt.git
cd makus-virt
docker build -t makus-virt .
docker run -d --name makus-virt \
  -p 5000:5000 -p 5001:5001 -p 5002:5002 \
  -v makus-virt-config:/app/config \
  -v makus-virt-logs:/app/logs \
  --restart unless-stopped \
  makus-virt
```

### Debian 패키지 (직접 빌드)
```bash
git clone https://github.com/dskim1979/makus-virt.git
cd makus-virt
dpkg-buildpackage -us -uc
sudo dpkg -i ../pegaprox_*.deb
```

## 🔄 업데이트

- **화면에서**: 설정 → 업데이트 → 업데이트 확인 (이 저장소에서 받음)
- **스크립트**:
  ```bash
  cd /opt/PegaProx
  sudo ./update.sh
  ```

## 🔧 처음 설정

1. 브라우저에서 `https://<서버 주소>:5000` 접속 (처음에는 자체 서명 인증서 경고를 허용 — 5001·5002 포트도 한 번씩)
2. **설정 마법사**에서 첫 관리자 계정을 만듭니다 (기본 계정·비밀번호는 없습니다)
3. 설정 → 클러스터 → Proxmox VE 주소와 계정(또는 API 토큰) 등록
4. 하드웨어 상태를 보려면 설정에서 하드웨어 모니터링 동의를 켭니다

## 📁 폴더 구조

```
/opt/PegaProx/
├── pegaprox_multi_cluster.py   # 실행 진입점
├── pegaprox/
│   ├── api/                    # REST API (korean_reports.py — 한국형 보고서)
│   ├── core/                   # 클러스터 관리·DB·캐시 (hw_history.py — 하드웨어 상태 이력)
│   ├── background/             # 수집·알림·예약 작업
│   ├── utils/                  # 인증·권한·LDAP·OIDC
│   └── models/
├── web/
│   ├── index.html              # 빌드된 화면
│   ├── src/                    # 화면 소스 (JSX)
│   └── reports-src/            # 한국형 보고서 양식·문서 변환 소스
├── static/                     # 내장 라이브러리 (격리망용), makus-reports.js
├── config/                     # 데이터베이스 (Linux x86_64 에서는 전체 암호화)
├── logs/
└── update.sh
```

## 🔒 보안

- 데이터베이스: SQLCipher(AES-256) 전체 암호화 (Linux x86_64), 그 밖의 환경은 민감 필드 암호화 — 자세한 내용 [docs/SECURITY.md](docs/SECURITY.md)
- 마스터 키: 환경 변수 / systemd 자격 증명(TPM2) / `/etc/pegaprox/secret.key` 순으로 읽고, 권한이 느슨한 파일은 쓰지 않음
- 비밀번호 Argon2id, API 토큰 SHA-256 해시
- 로그인·API 요청 횟수 제한, CSRF 출처 확인, 모든 API 에서 서버 측 권한 검사
- 운영 환경에서는 HTTPS 필수

## 🛠 개발

- 테스트: `pytest tests` (Linux)
- 화면 빌드: `bash web/Dev/build.sh`
- 한국형 보고서 양식·문서 변환 빌드: `bash web/reports-src/build.sh` (결과 `static/js/makus-reports.js` 도 함께 커밋)

## 💬 문의

- MOAVI: support@makussystems.co.kr · [GitHub Issues](https://github.com/dskim1979/makus-virt/issues)
- 원본 PegaProx 의 공통 기능 문의: [PegaProx 커뮤니티](https://github.com/PegaProx/project-pegaprox/issues)

## 📜 기반 프로젝트와 라이선스

MOAVI 는 **[PegaProx](https://pegaprox.com)** (Copyright © 2025-2026 PegaProx Team and contributors) 를 포크한 프로젝트입니다.
멀티 클러스터 관리의 핵심 기능은 PegaProx 팀의 작업이며, MOAVI 가 더한 기능은 위 표에 정리했습니다.
PegaProx 가 유용하셨다면 [원 개발팀을 후원](https://github.com/PegaProx/project-pegaprox)해 주세요.

- 라이선스: **GNU AGPL-3.0** — [LICENSE](LICENSE)
- **표시 의무 (AGPL 7조 b항)**: 고객 포털 화면에 표시되는 **"Powered by PegaProx"** 와 그에 딸린 저작권·소스·라이선스 안내는
  모든 복사본과 수정본에서 지우거나 숨길 수 없습니다 — [NOTICE](NOTICE)
- **소스 공개 (AGPL 13조)**: 수정한 버전을 네트워크로 다른 사람에게 제공하면 그 버전의 전체 소스를 제공해야 합니다.
  MOAVI 는 수정한 소스 전체를 이 저장소에 공개합니다.
- "MOAVI", "모아비" 및 관련 로고는 (주)매커스시스템즈의 상표입니다. PegaProx 는 PegaProx Team 의 프로젝트이며, Proxmox 는 Proxmox Server Solutions GmbH 의 상표입니다 (제휴 관계 아님).
- 한국형 보고서의 한글(HWPX) 기본 골격은 [python-hwpx](https://github.com/airmang/python-hwpx)(Apache-2.0)에서 가져왔습니다.
