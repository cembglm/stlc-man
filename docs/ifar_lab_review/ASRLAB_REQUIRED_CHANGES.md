# ASRLab Tarafında Gerekli Teknik Değişiklikler

## Hedef durum

ASRLab tarafında yeni bir izlenebilirlik sistemi kurulmasına gerek yoktur. Mevcut requirement set, submission manifest, deterministic verdict, result ingestion ve coverage çekirdeği korunmalı; eksik yaşam döngüsü orkestrasyonu ve IFARLAB contract conformance katmanı bu çekirdeğe eklenmelidir. Değişiklikler mevcut `session_history` ve STLC akışlarıyla geriye uyumlu olmalıdır.

Bu belge tasarım önerisidir; uygulama kodunda değişiklik yapılmamıştır.

## 1 Backend değişiklikleri

### 1.1 Entegrasyon kampanyası orkestrasyonu

Yeni bir `VerificationCampaign` kavramı eklenmelidir. Campaign, SUT sürümü ve requirement set sürümü için generation, submission, result, defect, regression ve RC aşamalarını birbirine bağlamalıdır.

Asgari alanlar:

- `campaign_id`, `sut_id`, `sut_version`, `source_sha256`
- `requirements_set_version`, `scenario_catalog_version`, `twin_config_version`
- suite revision ve iteration count
- mevcut state ve state transition geçmişi
- predecessor campaign ve regression baseline
- insan inceleme/engelleme nedeni

State machine dış servis çağrılarını idempotent event handler'larla yürütmelidir. Bir sonuç paketi yeniden geldiğinde yeni defect veya yeni kampanya oluşturmamalıdır.

### 1.2 Sonuç sonrası otomatik yönlendirme

`TraceabilityService.ingest_result` kalıcı kayıt ve karar yeniden hesaplamasıyla sınırlı kalmalı; transaction/outbox event yayınlamalıdır. Ayrı bir coordinator:

- `fail_cause=sut` için tekil defect açmalı;
- `test_artifact` için test revision/regeneration işi açmalı ve SUT defect oluşturmamalı;
- `infrastructure` için IFARLAB incident/notification kaydı üretmeli;
- contradiction veya verdict disagreement için insan inceleme işi açmalı;
- yeni SUT sürümünde tam regresyon campaign'i planlamalıdır.

Bu davranışlar synchronous HTTP request içinde dağınık yan etki olarak uygulanmamalıdır.

### 1.3 Karar motoru uyumlandırması

Danışman kararı sonrasında `verdict_engine.py` ve `config/ifarlab_contract_v1.json` tek decision table'dan üretilmeli veya aynı versioned kural paketini kullanmalıdır. Özellikle:

- reset failure sınıflandırması;
- timeout, missing evidence ve düşük RTF;
- code-quality failure'ın `fail_cause` etkisi;
- assertion/robot contradiction;
- SUT dışı FAIL'in requirement durumuna etkisi;
- STALE girdilerinin requirement, contract, SUT ve twin-config sürümleriyle ilişkisi

ortak golden vector setinde açıkça yer almalıdır.

### 1.4 RC ve terfi değerlendirme servisi

Mevcut `RCReport` modeline manuel veri göndermek yerine `ReleaseCandidateEvaluator` aşağıdaki değerleri kayıt sisteminden hesaplamalıdır:

- tüm Z QCR'lerin SUT sürümü bazındaki durumu;
- requirement coverage ve acceptance coverage;
- açık critical/high defect sayısı;
- mutasyon skoru ve onaylı eşik;
- güncel twin-fidelity reference ve geçerlilik süresi;
- contradiction/review sayısı;
- önceki sürüme göre regressions.

Değerlendirme atomik snapshot üretmeli, snapshot hash'i RC raporu ve promotion kaydına bağlanmalıdır.

### 1.5 Ters izlenebilirlik sorguları

Mevcut coverage detail API korunarak aşağıdaki explicit sorgular eklenmelidir:

- requirement -> test cases -> runs -> evidence -> verdicts;
- SUT release -> failed requirements -> defects;
- defect -> patch -> fixed SUT release -> regression verdict;
- deployment -> promotion -> RC -> SUT -> runs -> evidence -> requirements.

Her sorgu artifact ID, version, SHA-256 ve link status döndürmelidir. Eksik halka sessizce düşürülmemeli, `missing_links` olarak raporlanmalıdır.

## 2 API ve veri sözleşmesi değişiklikleri

### 2.1 Kanonik contract bundle

`config/ifarlab_contract_v1.json` ve ayrı şemalar tek sürümlü dağıtım paketi olarak yayımlanmalıdır. Paket şunları içermelidir:

- tüm JSON Schema dosyaları;
- kural seti ve golden vectors;
- test case prefix listesi;
- canonical JSON ve exact-byte hashing kuralları;
- compatibility matrix ve deprecation tarihleri;
- bundle SHA-256, tercihen dijital imza.

IFARLAB CI, bu paketin consumer conformance testlerini çalıştırmalıdır.

### 2.2 Genişletilecek veya eklenecek sözleşmeler

- `result.json`: contract, requirement set, SUT, twin config, scenario catalog, seed/planlayıcı parametreleri, verification level, clock, evidence ve input hash'leri zorunlu olmalıdır.
- `verdict.json`: `rule_set_version`, `inputs`, rule evaluation order, `fail_cause`, contradiction ve decision provenance içermelidir.
- `coverage.xml`: dil/tool metadata ve test case/run bağlantısı taşımalıdır.
- `scenario_catalog.json`: version, catalog hash, scenario ground truth ve varyasyon bilgisi.
- `twin_fidelity.json`: paired run IDs, metric deltas, approved tolerances, config hash, validity/expiry.
- `deployment.json`: cell, SUT, promotion, deployed/rolled-back timestamps ve physical verification references.
- `field_finding.json`: deployment, symptom/classification, evidence, candidate test linki.
- `review_decision.json`: contradiction/disagreement owner, decision, rationale, approver ve superseded verdict linki.

### 2.3 Transport ve acknowledgement

SSH inbox birincil yol olacaksa:

- upload `.partial` adla yapılmalı, fsync/atomic rename sonrası import edilmelidir;
- paket adı ve içerik ID'leri aynı olmalıdır;
- ASRLab `acknowledged|rejected` receipt üretmelidir;
- retry aynı package hash ve idempotency key'i kullanmalıdır;
- quarantine alanı ve retention politikası tanımlanmalıdır.

HTTP endpoint korunacaksa aynı şema, hash, authz ve idempotency politikası uygulanmalıdır; iki yol farklı semantik üretmemelidir.

## 3 Veritabanı ve şema değişiklikleri

### 3.1 Zorunlu indexler

Üretim başlangıcında doğrulanacak index manifesti hazırlanmalıdır. En az:

- `requirement_sets(requirements_set_version)` unique;
- `traceability_submissions(submission_id, revision)` unique;
- `ifarlab_result_deliveries(delivery_sha256)` unique ve `(submission_id, run_id, test_case_id)` sorgu indexi;
- `verification_verdicts(submission_id, run_id, test_case_id, evaluation_version)` unique veya explicit supersession modeli;
- lifecycle artifact ID'leri unique;
- coverage snapshot ID unique;
- campaign ID ve event id unique.

Uygulama katmanı kontrolleri korunmalı, ancak DB constraint'in yerine geçmemelidir.

### 3.2 Proje ve tarihsel kapsam

Global `is_current` requirement set yaklaşımı çok projeli kullanım için ayrıştırılmalıdır. Current selection en az `project_id + sut_id` scope'una taşınmalıdır. Tarihsel kayıtlar yeniden yazılmamalı; reviewed migration ile scope eklenmelidir.

### 3.3 Yeni koleksiyonlar

Gerekli minimum yeni koleksiyonlar:

- `verification_campaigns`
- `integration_outbox`
- `human_review_tasks`
- `deployment_records`
- `field_findings`

Mevcut requirement, submission, delivery ve verdict koleksiyonları çoğaltılmamalıdır.

## 4 Frontend değişiklikleri

Mevcut `TraceabilityDashboard` genişletilmelidir:

- SUT sürümü ve verification level filtreleri;
- requirement durumunun ölçüm, eşik, run ve kanıt gerekçesi;
- defect -> patch -> release closure görünümü;
- regression karşılaştırması;
- contradiction/disagreement inceleme kuyruğu;
- RC kriterleri ve hangi kriterin kapıyı engellediği;
- twin ve physical sonuçların yan yana gösterimi;
- deployment ve rollback bağlantıları;
- missing/unlinked/stale artifact uyarıları.

IFARLAB'ın canlı twin kamera ve scheduler ekranı ASRLab'a kopyalanmamalıdır. Ortak UX kararıyla özet health/status ve güvenli deep-link kullanılmalıdır.

Frontend için Vitest/React Testing Library testleri eklenmeli; yalnız build geçişi yeterli kabul edilmemelidir.

## 5 Verification kuralları

Kurallar kod içine dağılmamalı, sürümlü decision table ve test vektörleriyle yönetilmelidir. Asgari kurallar:

1. Admission geçmeden execution verdict üretilmez.
2. Invalid/incomplete evidence hiçbir zaman PASS olamaz.
3. Ölçülemeyen metrik sıfır değildir.
4. Unit uyuşmazlığı karar vermez; inconclusive veya schema error üretir.
5. `test_artifact` ve `infrastructure` FAIL, requirement'ı SUT FAIL yapmaz.
6. Aynı SUT, requirement, test-case ve environment scope'unda hangi koşunun “latest” olduğu deterministik tanımlanır.
7. Requirement, contract, SUT veya twin config değişimi ilgili evidence'ı STALE yapar.
8. Contradiction ve external/local verdict disagreement kapanmadan otomatik RC PASS üretilemez.

## 6 Raporlama ve KPI değişiklikleri

KPI raporu aşağıdaki ölçümleri ayrı göstermelidir:

- mapped requirement coverage;
- generated/executable coverage;
- valid DT executed coverage;
- verified DT coverage;
- acceptance-criterion coverage;
- functional ve non-functional paydaları;
- stale, unlinked, excluded ve inconclusive sayıları;
- SUT version ve verification level;
- synthetic/mock/live ayrımı.

FR %100 ve NFR %80 hedefleri resmi onay alınana kadar `configured_target`, proje başarısı ise `not_claimed` olarak raporlanmalıdır. LLM hiçbir KPI sayısını hesaplamamalı veya yeniden yazmamalıdır.

## 7 Entegrasyon testleri

### ASRLab tarafından bağımsız çalıştırılabilir

- schema/contract golden fixtures;
- hash, duplicate, path traversal, oversized package ve corrupt JSON negatif testleri;
- deterministic verdict vectors;
- requirement aggregation ve STALE vectors;
- cause routing ve idempotent defect creation;
- RC evaluator fixtures;
- Mongo unique index concurrency tests;
- frontend state/drill-down tests;
- API authn/authz negative tests.

### IFARLAB ile koordineli

- gerçek SUT package import ve exact hash;
- submission admission AT-05;
- gerçek twin evidence ile AT-01, AT-03 ve AT-04;
- injected SUT bug ve fix loop AT-02;
- twin-config change ve fidelity gate AT-06;
- physical smoke fail/rollback AT-07;
- deployment'tan QCR'ye AT-08;
- duplicate submission/result ve delivery retry;
- 16 twin isolation/load;
- üç gerçek reproducibility replay;
- restricted SSH account/ACL/firewall testleri.

## 8 IFARLAB bağımlılıkları

ASRLab'ın tamamlayamayacağı dış girdiler:

- kanonik SUT paket listesi ve dil/toolchain;
- scenario catalog ve ground truth;
- twin config registry ve fidelity üretimi;
- admission, scheduler, evidence recorder ve metric extractor;
- IFARLAB verdict engine conformance;
- 16 twin health/golden run;
- fiziksel deployment, smoke, rollback ve field finding;
- gerçek SSH account/network kurulumu;
- onaylı LLM sağlayıcı/model listesi.

## 9 Güvenlik değişiklikleri

- API key'e ek role-based authorization: importer, reviewer, release approver, auditor.
- Approval ve deployment gibi yüksek etkili kayıtlar için güçlü kullanıcı kimliği ve mümkünse artifact imzası.
- Secret'ların log ve event payload'larından çıkarılması; anahtar rotasyonu.
- Inbox hesabı ile uygulama hesabının ayrılması ve least-privilege ACL.
- Tar/JSON limitlerinin konfigürasyon ve alarm ile izlenmesi.
- Audit event'lerinde request ID, actor, source host ve immutable timestamp.

## 10 Geriye uyumluluk

Eski `session_history` akışı kaldırılmamalıdır. Legacy `exec-<uuid>.py` çağrıları geçiş süresince explicit `legacy_untraceable` olarak işaretlenmeli ve KPI'ya girmemelidir. Yeni zorunlu alanlar schema version yükseltilerek eklenmeli; eski kayıtlar uydurma provenance ile doldurulmamalıdır.
