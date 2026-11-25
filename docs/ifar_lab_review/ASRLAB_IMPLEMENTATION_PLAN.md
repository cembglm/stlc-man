# ASRLab IFARLAB Uygulama Planı

## Planlama ilkesi

Plan, mevcut izlenebilirlik çekirdeğini koruyarak ilerler. Önce ortak kararlar ve sözleşme sabitlenir; ardından ASRLab'ın bağımsız tamamlayabileceği kalıcılık ve orkestrasyon işleri yapılır; gerçek IFARLAB entegrasyonu daha sonra ortak kabul senaryolarıyla doğrulanır. Hiçbir faz, sentetik veya mock sonucu gerçek dijital ikiz kanıtı olarak raporlamaz.

Karmaşıklık: S, M, L, XL. Risk: düşük, orta, yüksek, kritik.

## Faz 0 Mimari karar ve sözleşme dondurma

| ID | İş | Bağımlılık | Depo değişikliği | Kabul ölçütü | Otomatik test | Koordinasyon | Karmaşıklık | Risk |
|---|---|---|---|---|---|---|---|---|
| P0-01 | SUT kapsamını tek tanıma bağla | Danışman/IFARLAB | Contract ve tasarım dokümanı; kod sonra | QC-only veya ROS2+Gazebo tanımı imzalı karar kaydında | Schema examples her tanıma göre doğrulanır | Ortak | S | Kritik |
| P0-02 | Reset ve validity decision table'ını onayla | P0-01 | `config/ifarlab_contract_v1.json`, verdict vectors | Reset/timeout/RTF/missing evidence için tek beklenen sonuç | Exhaustive parameterized golden vectors | Ortak | M | Kritik |
| P0-03 | Eşikleri onayla | Ölçüm/akademik karar | Versioned config | RTF, mutation, retry, iteration değerleri ve owner belli | Boundary tests | Ortak | S | Yüksek |
| P0-04 | Contract bundle 1.2 hazırla | P0-01..03 | `config/ifarlab_schemas/v1.2/`, bundle manifest | Tüm şemalar, rules, prefixes ve vectors aynı hash ile dağıtılır | Producer/consumer conformance | Ortak | M | Yüksek |
| P0-05 | Transport ve güvenlik kararını kaydet | Güvenlik/operasyon | ADR ve config şeması | SSH/HTTP rolleri, authn, authz, ack, signing net | Threat-focused negative fixture planı | Ortak | S | Yüksek |

Entegrasyon checkpoint C0: ASRLab ve IFARLAB aynı bundle SHA-256 ve golden vector sonuçlarını imzalı/izlenebilir kayıtla doğrular.

## Faz 1 ASRLab veri bütünlüğü ve kapsam sertleştirme

Bu faz IFARLAB çalışır durumda olmadan tamamlanabilir.

| ID | İş | Bağımlılık | Depo değişikliği | Kabul ölçütü | Otomatik test | Koordinasyon | Karmaşıklık | Risk |
|---|---|---|---|---|---|---|---|---|
| P1-01 | Mongo index manifesti ve startup doğrulaması | - | database initialization, index config | Tüm artifact ID ve delivery hash constraintleri aktif | Concurrent duplicate tests | Bağımsız | M | Yüksek |
| P1-02 | Requirement set'i project+SUT scope'una taşı | P1-01 | model/service/query filters | İki proje current set'i birbirini etkilemez | Multi-project fixtures | Bağımsız | M | Orta |
| P1-03 | Artifact reference modelini standartlaştır | P0-04 | shared models | Her link ID, version, hash, relation type taşır | Model/schema tests | Bağımsız | M | Orta |
| P1-04 | Result/verdict input hash setini zorunlu yap | P0-04 | traceability models, package service | Eksik veya değişmiş input hash red/unlinked olur | Tamper tests | Bağımsız | M | Yüksek |
| P1-05 | Deployment, field finding ve review modelleri | P0-04 | models/services/routes | Şemalı append-only kayıtlar ve links | CRUD immutability tests | Bağımsız | M | Orta |
| P1-06 | Legacy kayıtları explicit ineligible işaretle | - | coverage exclusions | Legacy provenance KPI'ya girmez | Historical fixture tests | Bağımsız | S | Orta |

Checkpoint C1: 100 eşzamanlı duplicate fixture denemesinde tek canonical kayıt; eski API akışlarında regresyon yok.

## Faz 2 ASRLab kampanya ve cause orkestrasyonu

Bu faz büyük ölçüde bağımsızdır; IFARLAB fixture'ları contract bundle üzerinden simüle edilir.

| ID | İş | Bağımlılık | Depo değişikliği | Kabul ölçütü | Otomatik test | Koordinasyon | Karmaşıklık | Risk |
|---|---|---|---|---|---|---|---|---|
| P2-01 | `VerificationCampaign` state machine | P1-02,P1-03 | model/service/router | Illegal transition reddedilir; geçmiş append-only | State transition/property tests | Bağımsız | L | Yüksek |
| P2-02 | Transactional outbox/event worker | P1-01,P2-01 | outbox collection, worker | Crash/replay duplicate yan etki üretmez | Kill/restart/idempotency tests | Bağımsız | L | Yüksek |
| P2-03 | Cause router | P2-02,P0-02 | result event handlers | sut->defect, artifact->regeneration, infra->notification | AT-02/03 synthetic variants | Bağımsız | M | Kritik |
| P2-04 | Contradiction/disagreement review akışı | P1-05,P2-02 | review service/API | Açık review varken otomatik RC yok | RBAC and supersession tests | Bağımsız | M | Yüksek |
| P2-05 | Üretim retry ve escalation | P2-01,P0-03 | generation coordinator | Bütçe sonrası çağrı durur, insan görevi açılır | Provider-call-count tests | Bağımsız | M | Orta |
| P2-06 | Iteration budget ve regression campaign | P2-01,P0-03 | campaign coordinator | Yeni SUT tam suite; limitte escalation | Version regression fixtures | Bağımsız | L | Yüksek |

Checkpoint C2: AT-02 ve AT-03 sentetik contract fixture'ları doğru cause routing, duplicate koruması ve audit zinciriyle geçer.

## Faz 3 Kapsam optimizasyon ve raporlama

| ID | İş | Bağımlılık | Depo değişikliği | Kabul ölçütü | Otomatik test | Koordinasyon | Karmaşıklık | Risk |
|---|---|---|---|---|---|---|---|---|
| P3-01 | Unified optimization report | P1-03 | optimization/coverage services | Before/after requirement, acceptance, branch ve mutation raporu | Coverage non-regression fixtures | Bağımsız | L | Orta |
| P3-02 | Survivor->new test döngüsü | P3-01,P0-01 | mutation adapters, generation events | Survivor lineage ile yeni test revision | Sandboxed mutant fixtures | SUT dili için ortak karar | L | Yüksek |
| P3-03 | RC evaluator ve immutable snapshot | P2-04,P2-06,P3-01 | lifecycle/report services | Tek eksik kriter RC'yi engeller | Full criterion matrix tests | Bağımsız | L | Kritik |
| P3-04 | Ters sorgu API'leri | P1-03,P1-05 | traceability router/service | TRC-05 dört sorgu missing-links ile döner | Graph fixture tests | Bağımsız | M | Orta |
| P3-05 | SUT bazlı teknik rapor | P3-03,P3-04 | reporting service | status, reason, rates, level, defects, regressions tek rapor | Golden JSON snapshots | Bağımsız | M | Orta |
| P3-06 | KPI hedef/iddia sınırı | P0-03 | coverage response/report | Configured target ve achieved claim ayrılır | Zero denominator/synthetic tests | Bağımsız | S | Orta |

Checkpoint C3: sentetik tam kampanya requirement'tan RC'ye izlenebilir; rapor hiçbir mock kaydı live KPI olarak saymaz.

## Faz 4 Frontend ve insan incelemesi

| ID | İş | Bağımlılık | Depo değişikliği | Kabul ölçütü | Otomatik test | Koordinasyon | Karmaşıklık | Risk |
|---|---|---|---|---|---|---|---|---|
| P4-01 | SUT/version/level filtreleri | P3-05 | TraceabilityDashboard | Filtre backend scope ile aynı sonucu verir | Component/API mock tests | Bağımsız | M | Düşük |
| P4-02 | Defect-patch-release ve regression görünümü | P3-04 | yeni lifecycle views | Zincir ve missing link görünür | Component snapshot/user tests | Bağımsız | M | Orta |
| P4-03 | Review kuyruğu ve karar formu | P2-04 | review components | Yetkili karar audit kaydı üretir | RBAC/UI tests | Bağımsız | M | Yüksek |
| P4-04 | RC gate ve evidence drill-down | P3-03 | release view | Engelleyen kriter ve evidence gösterilir | Acceptance tests | Bağımsız | M | Orta |
| P4-05 | Twin/physical/deployment karşılaştırması | P1-05,P3-04 | comparison view | Aynı QCR satırında iki verification level | Contract mock tests | IFAR veri alanlarıyla ortak | M | Orta |

Checkpoint C4: akademik danışman ve doğrulama mühendisi, örnek kampanyada requirement gerekçesi, contradiction ve RC engelini UI'dan açıklayabilir.

## Faz 5 IFARLAB kontrat entegrasyonu

Bu faz gerçek IFARLAB geliştirmesi olmadan tamamlanamaz.

| ID | İş | Bağımlılık | Depo değişikliği | Kabul ölçütü | Otomatik test | Koordinasyon | Karmaşıklık | Risk |
|---|---|---|---|---|---|---|---|---|
| P5-01 | Producer/consumer contract CI | C0 | CI pipelines | Aynı bundle ve fixtures iki tarafta geçer | Cross-repo conformance | Ortak | M | Kritik |
| P5-02 | Gerçek SSH inbox ve receipt | P0-05,P1-04 | deployment config/runbook | Restricted account yalnız inbox'a yazar | ACL/firewall/duplicate tests | Ortak | L | Kritik |
| P5-03 | Gerçek SUT ve scenario package | P0-01,P0-04 | fixture registry | Hash ve ID zinciri iki uçta aynı | AT-05 plus happy admission | Ortak | M | Yüksek |
| P5-04 | Evidence/metrics/coverage ingestion | P5-03 | parser/schema refinements | ROS evidence refs, sim clock, coverage bağlanır | Known-scene metrics tests | Ortak | XL | Kritik |
| P5-05 | Ortak verdict conformance | P0-02,P5-04 | rule package if needed | Golden ve gerçek run'da aynı karar | Differential tests | Ortak | L | Kritik |
| P5-06 | Duplicate/retry/recovery | P5-02 | transport handling | Network interruption yeni run yaratmaz | Fault injection | Ortak | M | Yüksek |

Checkpoint C5: AT-01, AT-03, AT-04 ve AT-05 gerçek twin entegrasyonunda geçer; result package ve ASRLab yeniden kararı eşleşir.

## Faz 6 Hata döngüsü ve regresyon

| ID | İş | Bağımlılık | Depo değişikliği | Kabul ölçütü | Otomatik test | Koordinasyon | Karmaşıklık | Risk |
|---|---|---|---|---|---|---|---|---|
| P6-01 | Enjekte SUT hatası kampanyası | C5,P2-03 | test data only | SUT FAIL tek defect açar | AT-02 live | Ortak | L | Kritik |
| P6-02 | Patch approval ve yeni SUT bağlantısı | P6-01 | integration glue | Onaylı patch yeni release fixes alanına bağlanır | Negative approval plus live release | Ortak | M | Yüksek |
| P6-03 | Tam regresyon ve gerileme raporu | P6-02,P2-06 | report refinements | Önceki PASS->yeni FAIL ayrıca listelenir | Cross-version comparison | Ortak | L | Yüksek |
| P6-04 | Mutation sample in twin | P5-04,P3-02 | adapter config | Onaylı sample güvenli koşar | Isolation/resource tests | Ortak | XL | Kritik |

Checkpoint C6: AT-02 tam zincir D->P->yeni SUT->regression verdict olarak sorgulanabilir.

## Faz 7 Fidelity fiziksel terfi ve saha döngüsü

| ID | İş | Bağımlılık | Depo değişikliği | Kabul ölçütü | Otomatik test | Koordinasyon | Karmaşıklık | Risk |
|---|---|---|---|---|---|---|---|---|
| P7-01 | Twin fidelity kayıt tüketimi | P5-04,P3-03 | lifecycle integration | Güncel fidelity yoksa RC/promotion engelli | AT-06 contract test | Ortak | M | Kritik |
| P7-02 | Human promotion ve physical result | P4-04,P7-01 | deployment integration | Onaysız deploy yok; physical result aynı zincirde | Approval negative tests | Ortak | L | Kritik |
| P7-03 | Rollback ve deviation | P7-02 | deployment/deviation services | Physical fail rollback ve calibration review açar | AT-07 | Ortak | L | Kritik |
| P7-04 | Deployment reverse trace | P7-02,P3-04 | query/report | DEP->QCR zinciri tek rapor | AT-08 | Ortak | M | Yüksek |
| P7-05 | Field finding->test candidate | P7-02,P1-05 | finding/generation integration | Candidate finding ID'yi korur | Lineage tests | Ortak | M | Orta |

Checkpoint C7: AT-06, AT-07 ve AT-08 gerçek veya onaylı HIL/physical ortamda tamamlanır.

## Faz 8 Performans güvenlik ve kabul

| ID | İş | Bağımlılık | Depo değişikliği | Kabul ölçütü | Otomatik test | Koordinasyon | Karmaşıklık | Risk |
|---|---|---|---|---|---|---|---|---|
| P8-01 | 16 twin isolation/load | IFAR scheduler hazır | ölçüm scriptleri/config | Bir twin çökünce diğerleri sürer | Chaos/load suite | Ortak | L | Kritik |
| P8-02 | Reproducibility audit | P5-04 | report support | Üç rastgele run tolerans içinde tekrar | Replay suite | Ortak | M | Yüksek |
| P8-03 | RBAC, signing ve key rotation | P0-05 | auth/security services | Yetkisiz approval/deploy mümkün değil | Security negative tests | Ortak | L | Kritik |
| P8-04 | Tam regresyon | Tüm fazlar | CI | Eski STLC akışları ve yeni akışlar geçer | Backend suite, frontend tests/build | Bağımsız + ortak | L | Yüksek |
| P8-05 | 53 gereksinim ve AT kabul paketi | P8-01..04 | docs/evidence index | Her satırın gerçek evidence linki ve owner sign-off'u | RTM completeness checker | Ortak | M | Kritik |

Nihai checkpoint C8: 53 gereksinim matrisi gerçek kanıtla güncellenmiş, AT-01...AT-08 tamamlanmış, açık kritik karar kalmamış ve danışman onayı alınmıştır.

## Bağımsız ve koordineli işlerin özeti

ASRLab bağımsız tamamlayabilir: P1'in tamamı, P2'nin tamamı, P3-01/03/04/05/06, P4-01...04 ve sentetik/contract testleri. P3-02 SUT dili kararına, P4-05 IFAR alanlarına bağlıdır.

IFARLAB koordinasyonu gerektirir: P0 mimari kararları, P5'in tamamı, P6 canlı hata/regresyon, P7 fidelity/physical/deployment ve P8 load/reproducibility/security kabulü.

## Uygulama sırası ve durdurma koşulları

- C0 tamamlanmadan iki tarafta paralel API geliştirmesi yapılmamalıdır; aksi halde karar semantiği ayrışır.
- DB index ve idempotent outbox tamamlanmadan otomatik defect/patch/regression yan etkileri açılmamalıdır.
- Gerçek IFARLAB conformance kanıtı olmadan IMPLEMENTED_AND_VERIFIED statüsü IFARLAB sorumluluklarına verilmemelidir.
- Reset ve SUT kapsamı çelişkisi çözülmeden ortak kabul raporu yayımlanmamalıdır.
- Fidelity ve insan onayı doğrulanmadan fiziksel terfi otomasyonu etkinleştirilmemelidir.
