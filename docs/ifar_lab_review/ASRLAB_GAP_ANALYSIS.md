# ASRLab IFARLAB Gereksinim İzlenebilirlik Matrisi ve Boşluk Analizi

## Sonuç

Görev tanımındaki 53 gereksinimin 4'ü mevcut ASRLab kapsamı içinde uygulanmış ve yerel test kanıtıyla doğrulanmıştır. 27 gereksinim kısmen uygulanmıştır, 3 gereksinim uygulanmamıştır ve 19 gereksinim IFARLAB ortamı veya kanıtı bulunmadığı için bloke durumdadır. Gerçek dijital ikiz veya fiziksel robot kanıtı bulunmadığından hiçbir IFARLAB yürütme gereksinimi doğrulanmış sayılmamıştır.

| Durum | Sayı |
|---|---:|
| IMPLEMENTED_AND_VERIFIED | 4 |
| IMPLEMENTED_NOT_VERIFIED | 0 |
| PARTIALLY_IMPLEMENTED | 27 |
| NOT_IMPLEMENTED | 3 |
| BLOCKED | 19 |
| REQUIRES_CLARIFICATION | 0 |
| Toplam | 53 |

`REQUIRES_CLARIFICATION` sayısının sıfır olması açık karar olmadığı anlamına gelmez. RTF, mutasyon, yeniden üretim ve iterasyon eşikleri ile reset sınıflandırması, ilgili satırlarda kısmi durumun tamamlanmasını engelleyen danışman kararlarıdır.

## Kanıt ve uygulama referans kataloğu

Matrisi okunabilir tutmak için aşağıdaki kısa kodlar kullanılmıştır. Her kod gerçek depo yolu ve sembole karşılık gelir.

| Kod | Depo kanıtı |
|---|---|
| C1 | `backend/routers/traceability_router.py`: `import_requirements`, `import_sut_release`, `create_submission`, `ingest_result`, `import_result_package`, coverage rota ailesi |
| C2 | `backend/models/traceability.py`: `RequirementSet`, `SubmissionManifest`, `IFARLABResult`, `ExecutionEnvironment` |
| C3 | `backend/services/traceability_service.py`: `save_requirement_set`, `save_submission`, `ingest_result`, `dashboard` |
| C4 | `backend/services/traceability_contract.py`: canonical hashing, `validate_manifest_mapping` |
| C5 | `backend/services/verdict_engine.py`: `evaluate_test`, `aggregate_requirement` |
| C6 | `backend/services/requirement_coverage_service.py`: `calculate_requirement_coverage`, `RequirementCoverageService` |
| C7 | `backend/services/ifarlab_package_service.py`: güvenli `result.tar` okuma; `backend/services/execution_client.py`: SSH/HTTP adapterleri |
| C8 | `backend/services/sut_package_service.py`: SUT paket/hash/sürüm doğrulaması |
| C9 | `backend/models/ifarlab_lifecycle.py`, `backend/services/lifecycle_service.py`: defect, patch, RC, promotion kayıtları |
| C10 | `backend/mutation/`, `backend/services/mutation_*`: mutasyon üretimi ve değerlendirmesi |
| C11 | `backend/services/test_code_generation_service.py` ve mevcut requirement/test case/optimization servisleri |
| C12 | `frontend/src/components/traceability/TraceabilityDashboard.jsx`, `frontend/src/components/TabPanel.jsx` |
| C13 | `config/ifarlab_contract_v1.json`, `config/ifarlab_schemas/v1/` |
| C14 | `backend/services/llm_security_service.py`, `config/llm_sut_allowlist.json` |

Test kanıt kodları:

- E1: `backend/tests/test_sut_package_service.py`
- E2: `backend/tests/test_traceability_contract.py`, `test_requirement_set_immutability.py`
- E3: `backend/tests/test_traceability_ingestion.py`, `test_ifarlab_package_service.py`, `test_execution_submission_naming.py`
- E4: `backend/tests/test_verdict_engine.py`
- E5: `backend/tests/test_requirement_coverage_service.py`
- E6: `backend/tests/test_lifecycle_models.py`, mutasyon ve LLM güvenlik testleri

23 Kasım 2026 çalıştırma kanıtı: E1-E6 kapsamındaki seçili 89 test geçti; frontend production build 657 modülle geçti. Bunlar gerçek IFARLAB E2E kanıtı değildir.

KPI sütunundaki `KPI3.4` yalnız depo içindeki KPI 3.4 tasarımına göre gereksinim kapsamı/doğrulamasıyla ilişkilidir. Görev tanımında resmi MATISSE KPI eşlemesi açık verilmediği için diğer satırlar `-` olarak işaretlenmiştir.

## INT Girdiler ve arayüzler

| ID | Kaynak | Kısa gereksinim | Sorumlu | KPI | Mevcut uygulama ve kanıt | Durum | Eksik ve etki | Gerekli değişiklik | Kabul ve önerilen doğrulama | Öncelik |
|---|---|---|---|---|---|---|---|---|---|---|
| INT-01 | Görev tanımı 5.1 | SUT arşivi, release ve QCR paketi alınır; hash doğrulanır. | A | - | C1,C8; E1 | IMPLEMENTED_AND_VERIFIED | Gerçek IFARLAB paketiyle operasyonel test yok. | Kanonik paket örneği ve üretim boyut limitini ortaklaştır. | Gerçek/bozuk arşiv kontrat testi ve sahada dry-run. | Z |
| INT-02 | 5.1 | `sut_id/version/commit/source_sha256` değişmezdir. | O | - | C8,C9; E1 | PARTIALLY_IMPLEMENTED | ASRLab aynı sürüm farklı hash'i reddediyor; IFARLAB yayınlayıcı kanıtı yok. | IFARLAB release pipeline'ına aynı kural ve unique index eklenmeli. | İki uçta aynı negatif vektör; yarış koşulu testi. | Z |
| INT-03 | 5.1 | Tüm veri sürümlü JSON Schema ile aktarılır. | O | - | C2,C13; E2,E3 | PARTIALLY_IMPLEMENTED | Beş paylaşım şeması var; bütün lifecycle dosyaları ve iki uçta byte-identical dağıtım kanıtı yok. | Tek versioned contract bundle, compatibility policy ve CI consumer testleri. | Aynı fixture seti iki laboratuvarda aynı sonucu üretmeli. | Z |
| INT-04 | 5.1 | SSH ve yalnız inbox'a yazabilen hesap. | O | - | C7; E3 yalnız güvenli okuyucu | PARTIALLY_IMPLEMENTED | Windows OpenSSH hesabı, ACL, firewall ve negatif erişim testi yok. | Restricted account kurulum runbook'u ve kimlik rotasyonu. | Sahada inbox dışına yazma negatif testi ve audit log. | Z |
| INT-05 | 5.1 | Tekrar paket yeni koşu/ithal oluşturmaz. | B | - | C3,C7; E3 idempotent replay | PARTIALLY_IMPLEMENTED | ASRLab sonucu idempotent alır; IFARLAB submission idempotency kanıtı yok. | İki yönlü idempotency key ve acknowledgement protokolü. | Aynı submission/result 2 kez; tek run/tek delivery assert'i. | Z |

## TRC İzlenebilirlik

| ID | Kaynak | Kısa gereksinim | Sorumlu | KPI | Mevcut uygulama ve kanıt | Durum | Eksik ve etki | Gerekli değişiklik | Kabul ve önerilen doğrulama | Öncelik |
|---|---|---|---|---|---|---|---|---|---|---|
| TRC-01 | 5.2 | Tüm zincir kimlik/hash ile bağlanır. | O | KPI3.4 | C2-C9,C13; E1-E5 | PARTIALLY_IMPLEMENTED | Requirement->verdict çekirdeği var; defect->patch->release->RC->promotion->deployment zinciri dashboard'a bağlı değil. | Ortak artifact reference modeli ve ters sorgu API'leri. | DEP kaydından QCR'ye tek entegrasyon testi. | Z |
| TRC-02 | 5.2 | Kayıtlar append-only; üzerine yazılmaz. | O | - | C3,C8,C9; E1,E2,E3 | PARTIALLY_IMPLEMENTED | Uygulama kontrolü var; tüm koleksiyonlarda DB unique index/migration yok. | Üretim index manifesti ve startup health check. | Eşzamanlı duplicate write testi. | Z |
| TRC-03 | 5.2 | Her test case en az bir QCR'ye bağlıdır. | A | KPI3.4 | C1,C4; E2 | IMPLEMENTED_AND_VERIFIED | QCR submission kapısında uygulanıyor. | Native tüm üretim yollarının aynı kapıyı kullandığını CI'da zorla. | Bağsız test 422; bağlı test kabul. | Z |
| TRC-04 | 5.2 | QCR x test case x SUT matrisi üretilir. | O | KPI3.4 | C6,C12; E5 | PARTIALLY_IMPLEMENTED | Mevcut matris requirement version ve code/run içeriyor; SUT sürümü ana görünümde eksik/opsiyonel. | SUT boyutunu zorunlu filtre ve kolona ekle. | Tek sorguda üç boyut ve historical sürüm testi. | Z |
| TRC-05 | 5.2 | Dört ters sorgu panel ve raporda cevaplanır. | O | KPI3.4 | C6,C12; E5 | PARTIALLY_IMPLEMENTED | QCR->test mevcut; sürüm FAIL, defect closure ve deployment evidence sorguları tamam değil. | Dört ayrı drill-down endpoint ve UI görünümü. | AT-08 fixture'ı ve gerçek kayıtla rapor karşılaştırması. | Z |

## GEN Test üretimi ve optimizasyon

| ID | Kaynak | Kısa gereksinim | Sorumlu | KPI | Mevcut uygulama ve kanıt | Durum | Eksik ve etki | Gerekli değişiklik | Kabul ve önerilen doğrulama | Öncelik |
|---|---|---|---|---|---|---|---|---|---|---|
| GEN-01 | 5.3 | QCR, SUT ve capabilities'den case/pytest üret. | A | KPI3.4 | C11,C1,C14; E2,E6 | PARTIALLY_IMPLEMENTED | Parçalar var; zorunlu tüm QCR'leri kapsayan tek orkestrasyon kanıtı yok. | QCR import->generation->submission pipeline ve gap gate. | Z QCR başına en az bir bağlı case; fixture+integration. | Z |
| GEN-02 | 5.3 | Expected/oracle QCR/katalogdan gelir, LLM belirlemez. | A | - | C1,C2; ilgili router negatif testleri | IMPLEMENTED_AND_VERIFIED | QCR alan eşitliği submission kapısında zorlanıyor. | Scenario catalog kaynağı da hash'li referans olmalı. | Değiştirilmiş oracle 422; aynı oracle kabul. | Z |
| GEN-03 | 5.3 | Model/sürüm/temperature/prompt hash/tarih manifestte. | A | - | C2,C4; E2 | IMPLEMENTED_AND_VERIFIED | Alanlar ve “uydurmama” testi mevcut. | Provider approval ID ve prompt template version eklenebilir. | Manifest schema ve null provenance negatif testleri. | Z |
| GEN-04 | 5.3 | Validator/lint geçmeden gönderme; en çok 3 yeniden üretim. | A | - | C1,C2,C11; E2 | PARTIALLY_IMPLEMENTED | Gönderim kapısı var; üç deneme ve human-review state machine yok. | Konfigüre retry budget, attempt record ve review queue. | 3 başarısız üretim sonrası ağ çağrısı durmalı ve görev açılmalı. | Z |
| GEN-05 | 5.3 | Requirement/acceptance/branch/mutation ile optimize et; kapsam düşmesin. | A | KPI3.4 | C6,C10,C11; E5,E6 | PARTIALLY_IMPLEMENTED | Ölçüm motorları ayrı; tek optimizasyon kapısı ve before/after acceptance coverage garantisi yok. | Unified optimization report ve non-regression invariant. | Aynı fixture'da hiçbir kapsam metriği düşmemeli. | Z |
| GEN-06 | 5.3 | SUT mutasyonu; survivor için yeni test. | A | - | C10; E6 | PARTIALLY_IMPLEMENTED | Mutasyon çekirdeği var; gerçek IFARLAB SUT dili/adapteri ve survivor->generation döngüsü yok. | Dil adapteri, sandbox execution, survivor event bağlantısı. | Mutant fixture öldürme ve survivor'dan yeni case entegrasyonu. | İ |
| GEN-07 | 5.3 | Catalog scenario ve ground truth kullanılır. | O | KPI3.4 | C1,C2; inspection için SC-NNN kapısı | PARTIALLY_IMPLEMENTED | Katalog şeması, good/defective çift ve hash/version doğrulaması yok. | `scenario_catalog.json` şeması ve manifest reference. | Her defect türü için iyi+kötü senaryo kontrat testi. | Z |

## TWN Dijital ikiz

| ID | Kaynak | Kısa gereksinim | Sorumlu | KPI | Mevcut uygulama ve kanıt | Durum | Eksik ve etki | Gerekli değişiklik | Kabul ve önerilen doğrulama | Öncelik |
|---|---|---|---|---|---|---|---|---|---|---|
| TWN-01 | 5.4 | Twin config sürümlenir ve hash koşuya yazılır. | B | - | ASRLab sonucu provenance alanı alabilir; IFAR kodu/kanıtı yok. | BLOCKED | Gerçek config ve STALE tetikleme kanıtı yok. | IFARLAB config registry ve result contract alanı. | Config değişiminde eski karar STALE; ortak E2E. | Z |
| TWN-02 | 5.4 | Scenario catalog ground truth ile sürümlenir. | B | KPI3.4 | Yalnız ASRLab scenario ID modeli. | BLOCKED | IFARLAB katalog artefaktı yok. | Katalog repo/registry ve imzalı hash. | Her QCR defect türü coverage testi. | Z |
| TWN-03 | 5.4 | 16 twin eşdeğer; günlük golden run. | B | - | Kanıt yok. | BLOCKED | Health/quarantine ve golden baseline yok. | IFARLAB scheduler, golden suite, quarantine state. | Sapmış twin'e iş atanmadığını fault injection ile doğrula. | Z |
| TWN-04 | 5.4 | Twin fidelity fiziksel/ikiz karşılaştırması. | B | - | RC modelinde reference alanı var; kayıt üretimi yok. | BLOCKED | Ölçüm yöntemi ve gerçek kayıt yok. | `twin_fidelity.json` şeması, tolerans ve expiry. | Config değişince terfi bloke; fiziksel/twin paired test. | Z |
| TWN-05 | 5.4 | Headless twin, camera panel, seçili GUI. | B | - | ASRLab Traceability UI bu işlevi sağlamaz. | BLOCKED | IFARLAB panel erişimi/kanıtı yok. | IFARLAB monitoring API; ASRLab yalnız deep-link/özet. | 16 durum, camera stream ve GUI quota testi. | İ |

## EXE Koşu ve kanıt

| ID | Kaynak | Kısa gereksinim | Sorumlu | KPI | Mevcut uygulama ve kanıt | Durum | Eksik ve etki | Gerekli değişiklik | Kabul ve önerilen doğrulama | Öncelik |
|---|---|---|---|---|---|---|---|---|---|---|
| EXE-01 | 5.5 | IFARLAB admission hash/manifest/QCR/contract/SUT/validator kontrolü. | B | - | ASRLab C1,C4 aynı kontrollerin bir kısmını yapar. | BLOCKED | IFARLAB admission implementasyonu ve red cevabı kanıtı yok. | Paylaşılan validator veya consumer conformance suite. | AT-05'i iki uçta çalıştır. | Z |
| EXE-02 | 5.5 | SUT hash kurulum, dış kanıt, tek tek koşu/reset. | B | KPI3.4 | ASRLab result modeli alanları alabilir. | BLOCKED | Gerçek env/reset/evidence yok. | IFARLAB harness ve immutable run directory. | Her case için install/hash/start/stop/reset log assert'i. | Z |
| EXE-03 | 5.5 | Tek koşu, otomatik retry yok, seed kaydı. | B | - | ASRLab idempotent result; seed modeli zorunlu değil. | BLOCKED | IFAR scheduler ve seed provenance kanıtı yok. | Result/env schema'ya zorunlu seed/params. | Aynı girdiler yeni run_id ile tolerans içi tekrar. | Z |
| EXE-04 | 5.5 | Case bazlı sim-time metrik; ölçülemeyen null. | B | KPI3.4 | `MetricValue` unavailable->null kuralı var. | BLOCKED | Clock alanı ve gerçek extractor kanıtı yok. | Metric envelope'a test_case_id/clock/source zorunluluğu. | Eksik ölçümün 0'a dönüşmediği extractor testi. | Z |
| EXE-05 | 5.5 | SUT çıktısını ground truth ile karşılaştır, inspection metrikleri üret. | B | KPI3.4 | ASRLab generic metric kabul eder. | BLOCKED | IFAR extractor ve ground-truth join yok. | Standard inspection metric schema. | Bilinen iyi/kusurlu fixture ile confusion metrikleri. | Z |
| EXE-06 | 5.5 | Test case bazında SUT code coverage. | B | - | ASRLab package reader coverage üyesini kanonik olarak zorlamıyor. | BLOCKED | IFAR coverage aracı ve dil kararı yok. | `coverage.xml` package contract ve parser. | Her case için valid report; eksikse NOT_VERIFIED. | Z |
| EXE-07 | 5.5 | RTF<0.7 veya kanıt eksikse INCONCLUSIVE. | B | KPI3.4 | C5; E4 yerel vektör geçiyor. | BLOCKED | Gerçek IFAR ölçümü yok; reset davranışı final tasarımla çelişkili. | Ortak validity vector suite ve onaylı reset kuralı. | AT-04 iki tarafta byte-equal verdict. | Z |

## VRD Karar

| ID | Kaynak | Kısa gereksinim | Sorumlu | KPI | Mevcut uygulama ve kanıt | Durum | Eksik ve etki | Gerekli değişiklik | Kabul ve önerilen doğrulama | Öncelik |
|---|---|---|---|---|---|---|---|---|---|---|
| VRD-01 | 5.6 | Deterministik ortak motor; LLM/eval yok. | O | KPI3.4 | C5,C13; E4 | PARTIALLY_IMPLEMENTED | ASRLab motoru doğrulandı; IFARLAB aynı commit/vector kanıtı yok. | Motoru versioned ortak paket veya golden vectors ile dağıt. | Aynı girdiden byte-normalized aynı verdict. | Z |
| VRD-02 | 5.6 | Validity->quality->robot->oracle->acceptance/assert; fail cause. | O | KPI3.4 | C3,C5; E4 | PARTIALLY_IMPLEMENTED | Sıra büyük ölçüde var; reset classification ve tüm cause kararları uyumsuz. | Onaylı decision table ve exhaustive vectors. | AT-01...04, her cause dalı. | Z |
| VRD-03 | 5.6 | SUT sürümü bazlı PASS/FAIL/NOT_VERIFIED/NOT_COVERED/STALE. | O | KPI3.4 | C5,C6; E4,E5 | PARTIALLY_IMPLEMENTED | SUT sürümü ve twin config STALE girdileri tüm zincirde zorunlu değil. | Aggregation scope'u SUT+twin+requirement version yap. | Aynı QCR iki SUT sürümünde farklı durum testi. | Z |
| VRD-04 | 5.6 | Verdict input hash'lerini taşır, ASR yeniden hesaplar. | O | - | C3-C5; E2-E4 | PARTIALLY_IMPLEMENTED | Yerel hash/link var; kanonik verdict schema ve IFAR byte paketi kanıtı yok. | `verdict.json.inputs` zorunlu hash seti. | Hash değiştirme negatif testi ve replay. | Z |
| VRD-05 | 5.6 | Assert-kanıt çelişkisi işaretlenir ve insan incelemesine düşer. | O | KPI3.4 | C5; E4 | PARTIALLY_IMPLEMENTED | Contradiction kayıtlı; assignment/resolution/supersession workflow yok. | Review entity, RBAC, karar ve audit trail. | Çelişki kapanmadan requirement PASS olmamalı. | Z |

## FIX Hata ayıklama döngüsü

| ID | Kaynak | Kısa gereksinim | Sorumlu | KPI | Mevcut uygulama ve kanıt | Durum | Eksik ve etki | Gerekli değişiklik | Kabul ve önerilen doğrulama | Öncelik |
|---|---|---|---|---|---|---|---|---|---|---|
| FIX-01 | 5.7 | Her SUT FAIL için kanıta bağlı defect aç. | A | - | C9; model/endpoint mevcut | PARTIALLY_IMPLEMENTED | Result ingestion otomatik defect açmıyor; duplicate policy yok. | Idempotent defect creation policy ve event handler. | AT-02'de tek defect, tam references. | Z |
| FIX-02 | 5.7 | Defect'ten patch öner; otomatik uygulama yok. | A | - | C9 patch/onay modeli | PARTIALLY_IMPLEMENTED | Patch generator ve insan iş kuyruğu yok. | Güvenli suggestion service, diff artifact, approval UI. | Onaysız patch applied olamaz. | Z |
| FIX-03 | 5.7 | Onaylı yama yeni SUT ve `fixes` listesi üretir. | B | - | C8 fixes referansını doğrular. | BLOCKED | IFARLAB release pipeline kanıtı yok. | IFAR release API/contract. | Bilinmeyen defect red; bilinen defect yeni sürüme bağlanır. | Z |
| FIX-04 | 5.7 | Yeni SUT'ta tam regresyon ve gerileme raporu. | O | KPI3.4 | Uygulama yok. | NOT_IMPLEMENTED | Yeni release tüm suite'i otomatik planlamıyor. | Regression campaign entity ve previous-version diff. | Eski PASS->yeni FAIL “regression” listesinde. | Z |
| FIX-05 | 5.7 | Test artifact FAIL yeniden üretime gider, defect açılmaz. | A | - | C3,C5 fail cause korur; E3,E4 | PARTIALLY_IMPLEMENTED | Otomatik regeneration dispatch ve negative defect guard yok. | Cause router ve lineage link. | AT-03: sıfır defect, yeni test revision. | Z |
| FIX-06 | 5.7 | En çok 5 iterasyon sonra insan kararı. | A | - | Uygulama yok. | NOT_IMPLEMENTED | Campaign/iteration sayacı ve review gate yok. | Configurable loop budget ve escalation. | 6. otomatik iterasyon başlatılmamalı. | İ |

## REL Sürüm adayı terfi ve gerçek robot

| ID | Kaynak | Kısa gereksinim | Sorumlu | KPI | Mevcut uygulama ve kanıt | Durum | Eksik ve etki | Gerekli değişiklik | Kabul ve önerilen doğrulama | Öncelik |
|---|---|---|---|---|---|---|---|---|---|---|
| REL-01 | 5.8 | RC çıkış kriterleri sağlanmadan rapor yok. | A | KPI3.4 | C9; E6 model gate | PARTIALLY_IMPLEMENTED | Kriterler DB'den otomatik ve atomik hesaplanmıyor; fidelity dış kayıt. | RC evaluator ve snapshot hash. | Eksik tek kriterde 422; tam fixture'da immutable RC. | Z |
| REL-02 | 5.8 | RC raporu SUT/verdict/evidence/closed defect/fidelity içerir. | A | KPI3.4 | C9, schema `rc_report`. | PARTIALLY_IMPLEMENTED | Otomatik rapor oluşturucu ve canonical report SHA yok. | Builder service ve schema export. | Rapor hash'i promotion ile birebir eşleşmeli. | Z |
| REL-03 | 5.8 | Fiziksel yükleme yalnız insan onayıyla. | O | - | C9; E6 | PARTIALLY_IMPLEMENTED | ASR model kapısı var; IFAR deploy enforcement ve RBAC yok. | İmzalı/kimlikli approval ve deploy consumer check. | Onaysız deployment negatif testi. | Z |
| REL-04 | 5.8 | Fiziksel smoke/fidelity aynı motorla kaydedilir. | B | KPI3.4 | Execution scope `physical_twin` alabilir. | BLOCKED | Fiziksel koşu kanıtı yok. | IFAR physical adapter ve ortak verdict bundle. | Twin/physical aynı QCR satırında. | Z |
| REL-05 | 5.8 | Uyuşmazlıkta rollback, sapma ve recalibration. | B | - | Uygulama kanıtı yok. | BLOCKED | Rollback/deviation contract yok. | Deployment/deviation/rollback şemaları ve event. | AT-07 fault injection. | Z |
| REL-06 | 5.8 | Deployment cell, SUT, tarih, promotion içerir. | B | - | ASR lifecycle modelinde deployment modeli yok. | BLOCKED | `deployment.json` tüketimi ve ters sorgu yok. | Deployment schema/API/index. | AT-08 zincir sorgusu. | Z |

## MON Panel raporlama ve sürekli kullanım

| ID | Kaynak | Kısa gereksinim | Sorumlu | KPI | Mevcut uygulama ve kanıt | Durum | Eksik ve etki | Gerekli değişiklik | Kabul ve önerilen doğrulama | Öncelik |
|---|---|---|---|---|---|---|---|---|---|---|
| MON-01 | 5.9 | Twin/camera/queue/matrix/SUT history paneli. | B | KPI3.4 | C12 yalnız ASR matrix/coverage. | BLOCKED | IFAR monitoring API/kanıtı yok; dört ters sorgu eksik. | Panel sorumluluğunu böl; IFAR operational, ASR evidence views. | Canlı twin fault ve TRC-05 UI acceptance. | Z |
| MON-02 | 5.9 | SUT başına status/reason/rates/level/open defects raporu. | A | KPI3.4 | C6,C12; E5 | PARTIALLY_IMPLEMENTED | Open defects, SUT version, verification level ve regression tek raporda eksik. | Versioned report DTO ve renderer. | Her sonuçtan sonra snapshot; fixture karşılaştırması. | Z |
| MON-03 | 5.9 | Saha bulgusu yeni test adayı olur. | O | - | Uygulama yok. | NOT_IMPLEMENTED | Finding ingestion ve lineage yok. | FieldFinding modeli/API; candidate generation linki. | Finding->candidate->test case zinciri. | İ |

## NFR Fonksiyonel olmayan gereksinimler

| ID | Kaynak | Kısa gereksinim | Sorumlu | KPI | Mevcut uygulama ve kanıt | Durum | Eksik ve etki | Gerekli değişiklik | Kabul ve önerilen doğrulama | Öncelik |
|---|---|---|---|---|---|---|---|---|---|---|
| NFR-01 | 5.10 | Case <=600 s; tam suite süresi raporlanır. | B | - | ASR remote adapter timeout taşıyor; gerçek koşu yok. | BLOCKED | IFAR enforcement ve suite duration kanıtı yok. | Contract alanı ve timing metrics. | Boundary 599/600/601 s testleri. | Z |
| NFR-02 | 5.10 | 16 twin paralel; bir çöküş diğerlerini etkilemez. | B | - | Kanıt yok. | BLOCKED | Load/isolation testi yok. | Scheduler isolation ve capacity test planı. | Bir twin kill edilirken 15 koşu sürmeli. | Z |
| NFR-03 | 5.10 | Aynı SUT/config/seed tolerans içinde yeniden üretilebilir. | O | - | Hash/provenance ve yeni run modeli kısmi. | PARTIALLY_IMPLEMENTED | Seed/config zorunlu değil; üç gerçek replay yok. | Reproducibility bundle ve tolerance policy. | Rastgele üç gerçek run replay. | Z |
| NFR-04 | 5.10 | SUT yalnız onaylı LLM'e gider; model kayıtlı. | O | - | C14,C2; E6 | PARTIALLY_IMPLEMENTED | ASR fail-closed allowlist var; gerçek IFAR onay kaydı ve policy signing yok. | Onay sahibi/tarih/scope, signed config ve audit. | Onaysız provider çağrısı ağ I/O'dan önce engellenmeli. | Z |

## Kritik mimari boşluklar

1. **Operasyonel entegrasyon kanıtı yok.** Yerel model ve testler güçlüdür; gerçek IFARLAB submission, `result.tar`, ROS evidence ve fiziksel hücre akışı doğrulanmamıştır.
2. **Karar kuralı çelişkisi vardır.** 23 Kasım final tasarımı reset hatasını `FAIL` sayar; mevcut motor ve test `INCONCLUSIVE` sayar. Aynı run iki tarafta farklı requirement durumuna yol açabilir.
3. **Yaşam döngüsü zinciri yarımdır.** Defect/patch/RC/promotion modelleri vardır; result ingestion'dan başlayan otomatik ve idempotent süreç yoktur. Deployment kaydı yoktur.
4. **Append-only garantisi DB seviyesinde tamam değildir.** Application check yarış koşullarına açıktır; production index/migration sözleşmesi yoktur.
5. **Güvenlik yalnız API key ve hash düzeyindedir.** Role-based authorization, imzalı artifact, anahtar rotasyonu ve restricted SSH sahası doğrulanmamıştır.
6. **IFARLAB contract consumer kanıtı yoktur.** Şema dosyaları ASRLab'da vardır fakat iki uçta aynı sürüm, byte ve verdict vector kullanıldığı gösterilmemiştir.
7. **Dashboard yaşam döngüsünü tamamlamaz.** Kapsam matrisi vardır; SUT history, defect closure, promotion/deployment, physical/twin ve review queue görünümü yoktur.

## Danışman onayı gerektiren kararlar

- Reset failure: `FAIL` mi `INCONCLUSIVE` mı; `fail_cause` sınıfları ve requirement agregasyon etkisi.
- SUT sınırı: 23 Kasım belgesindeki “Gazebo dahil ROS 2 yığını” tanımı ile görev tanımındaki “QC yazılımı SUT, robot ve ikiz ortamdır” ifadesi arasındaki çelişki.
- RTF minimumu 0.7, mutasyon hedefi %80, üretim retry 3 ve debug iterasyonu 5 değerlerinin bağlayıcılığı.
- Bağlayıcı kararın IFARLAB verdict'i olması halinde disagreement kapanış yetkisi ve override/supersession politikası.
- KPI 3.4 FR %100/NFR %80 hedeflerinin resmi MATISSE hedefi olup olmadığı.
- HTTP endpoint'in üretimde kalıp kalmayacağı veya SSH inbox'ın tek kanonik yol olup olmayacağı.
- Sözleşme bütünlüğü için SHA-256'nın yeterli olup olmadığı; imza/mTLS gereksinimi.
