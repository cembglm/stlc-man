# ASRLab Mevcut Uygulama İncelemesi

## Yönetici özeti

STLC Manager, ASRLab-IFARLAB entegrasyonu için boş bir başlangıç değildir. Depoda sürümlü gereksinim setleri, test-gereksinim eşlemesi, üretim provenance bilgisi, SHA-256 doğrulaması, güvenli sonuç paketi içe alma, deterministik kararın bağımsız yeniden hesaplanması, FR/NFR kapsam ölçümü, yaşam döngüsü kayıt modelleri ve bir React izlenebilirlik ekranı vardır. Seçili 89 backend testi ve frontend üretim derlemesi bu çekirdeğin yerel olarak çalıştığına dair kanıt sağlar.

Ancak mevcut kanıt, gerçek IFARLAB dijital ikizinde uçtan uca çalışmayı doğrulamaz. Twin havuzu, robot kanıtı, gerçek `result.tar` teslimi, fiziksel hücre terfisi ve saha geri beslemesi için operasyonel kanıt bulunmamaktadır. Bazı yaşam döngüsü kayıtları model ve endpoint düzeyindedir; otomatik orkestrasyon değildir.

## İncelenen kapsam ve kaynak durumu

İnceleme 23 Kasım 2026 tarihli çalışma ağacına ve aşağıdaki kaynaklara dayanır:

- `STLC_IFARLAB_Dijital_Ikiz_Dogrulama_Gorev_Tanimi.docx`: bulundu; 53 entegrasyon gereksinimi ve AT-01...AT-08 kabul senaryoları çıkarıldı.
- `Izlenebilirlik_Tasarim_18112026.docx`: bulundu.
- `Izlenebilirlik_Tasarim_18112026_oneriler (1).docx`: bulundu.
- `Izlenebilirlik_Tasarim_20112026_final.docx`: bulundu.
- Kullanıcının açıkça sağladığı `Izlenebilirlik_Tasarim_20112026_final (1).docx`: bulundu ve güncel mimari taban çizgisi olarak kullanıldı. Bu dosya 23 Kasım güncellemesidir ve suffixsiz dosyayla byte düzeyinde aynı değildir.
- Ayrı bir revize görev tanımı kopyası: bulunamadı.
- Açıkça “günlük geliştirme raporu” olarak adlandırılmış IFARLAB raporu: bulunamadı. `4 Eylül 2026 IFARLAB MATISSE Test Planı.docx` ve `IFARLAB_Coklu_Digital_Twin_Raporu.docx` yardımcı bağlamdır; günlük rapor yerine kabul edilmemiştir.

Kaynak belgelerde anlatılan davranışlar uygulama kanıtı sayılmamıştır. Özellikle final tasarımın “final” olarak işaretlenmesi, depodaki veya IFARLAB ortamındaki uygulamanın tamamlandığını göstermez.

## Backend API yüzeyi

Ana entegrasyon router'ı `backend/routers/traceability_router.py` içindedir ve `backend/app.py` tarafından uygulamaya eklenir. Bütün rotalar mevcut `require_api_key` bağımlılığını kullanır.

| Alan | Endpointler | Mevcut davranış | Kanıt düzeyi |
|---|---|---|---|
| Sözleşme | `GET /api/integrations/ifarlab/v1/contract` | Aktif sözleşmeyi ve byte tabanlı hash'i döndürür. | Birim testi var |
| Gereksinim seti | `POST /requirements`, `GET /requirements.json` | Tam, sürümlü seti saklar; aynı sürüm farklı içerikle yeniden kullanılamaz. | Birim testi var |
| SUT paketi | `POST /sut-releases/import` | Base64 arşiv, `sut_release` ve gereksinimleri doğrular; arşivi çalıştırmadan saklar. | Birim testi var |
| Gönderim | `POST /submissions`, manifest ve test kodu GET rotaları | AST, requirement ID, test case ID, kod hash'i, kontrat hash'i, QCR oracle ve kayıtlı SUT referansını doğrular. | Birim testi var |
| Sonuç | `POST /results`, `POST /inbox/{package_name}/import` | HTTP veya sınırlı SSH gelen kutusundaki güvenli tar paketini içe alır; kimlik ve hash bağlantısı kurar; yerel kararı yeniden hesaplar. | Mock/birim entegrasyon testi var |
| İzlenebilirlik | `GET /traceability`, `GET /report` | Gereksinim, test, yürütme ve karar görünümü üretir. | Servis testleri var |
| KPI kapsamı | `/coverage` rota ailesi | FR/NFR için mapped-generated-executable-executed DT-verified DT aşamalarını hesaplar; snapshot alabilir. | Kapsamlı sentetik testler var |
| Yaşam döngüsü | `POST /defects`, `/patches`, `/release-candidates`, `/promotions` | Şemalı ve değişmez kayıtlar; başarısız RC kriterini ve onaysız terfiyi reddeder. | Model/servis testleri var; otomatik akış yok |

## Veri modelleri ve sözleşmeler

`backend/models/traceability.py` şu temel modelleri içerir:

- `RequirementSet`, `Requirement`, `AcceptanceCriterion`: sürüm, tip, kabul kriteri, kaynak ve uygulanabilirlik bilgisi.
- `SubmissionManifest`, `ManifestTest`, `GenerationProvenance`, `CodeQuality`: exact code hash, model, prompt hash, test case, scenario ve requirement bağlantısı.
- `IFARLABResult`, `ExternalTestResult`, `ExecutionEnvironment`, `EvidenceReference`: dış koşu, ölçüm, kanıt ve ortam provenance bilgisi.
- `ExecutionScope`: `digital_twin`, `physical_twin`, `local`, `simulation`, `mock`, `unknown` ayrımını zorlar.

`backend/models/ifarlab_lifecycle.py` SUT sürümü, hata, yama, RC raporu ve insan onaylı terfi modellerini içerir. `config/ifarlab_schemas/v1/` altında paylaşım için JSON Schema dosyaları vardır. `config/ifarlab_contract_v1.json` karar durumlarını, kimlik biçimlerini, genel kuralları ve tasarım RTF eşiğini tanımlar.

Önemli sınırlama: modellerin bulunması, bu kayıtların sonuç içe alma sonrasında otomatik üretildiği anlamına gelmez. Hata açma, test artifact yeniden üretimi, regresyon planlama, RC ölçütlerini veri tabanından toplama ve saha bulgusu akışları uçtan uca orkestre edilmemiştir.

## Kalıcılık ve değişmezlik

`backend/services/traceability_service.py` şu MongoDB koleksiyonlarını kullanır:

- `requirement_sets`
- `traceability_submissions`
- `ifarlab_result_deliveries`
- `verification_verdicts`
- `traceability_events`
- `requirement_coverage_snapshots`

SUT ve yaşam döngüsü servisleri ayrıca SUT sürümü, hata, yama, RC ve terfi kayıtlarını saklar. Uygulama katmanı aynı kimliğin farklı içerikle üzerine yazılmasını reddeder; düzeltilmiş teslimler özgün teslimi ezmez.

Üretim riski: tüm koleksiyonlar için kalıcı MongoDB unique index ve migration/başlangıç doğrulaması gösterilmemiştir. Uygulama düzeyi kontrol yarış koşullarında tek başına yeterli değildir. Çok projeli kullanımda “current requirement set” seçimi globaldir; proje bazında ayrıştırılmamıştır.

## Test üretimi ve kod üretimi

Mevcut STLC akışları `backend/services/requirement_analysis_service.py`, `test_case_generation_service.py`, `test_case_optimization_service.py` ve `test_code_generation_service.py` üzerinden sürmektedir. Yeni izlenebilirlik katmanı bu akıştan gelen açık requirement ve scenario kimliklerini korur; tanımlanamayan prose'dan kimlik uydurmaz.

`create_submission` QCR akışında şunları zorlar:

- validator, lint ve toplam code-quality sonucu `pass` olmalıdır;
- her test case en az bir QCR'ye bağlı olmalıdır;
- inspection testlerinde `SC-NNN` scenario ID bulunmalıdır;
- `expected_outcome`, `expected_reason` ve `oracle` gereksinim kaydıyla aynı olmalıdır;
- kayıtlı ve hash'i eşleşen değişmez SUT sürümü bulunmalıdır.

Eksikler: üç denemelik yeniden üretim ve insan kuyruğu entegrasyon sözleşmesine bağlı değildir; senaryo kataloğunda iyi/kusurlu çift zorlaması yoktur; optimizasyon çıktısı ile zorunlu QCR kapsamasının düşmediğini garanti eden tek atomik kapı yoktur.

## Manifest, provenance ve bütünlük

`backend/services/traceability_contract.py` exact UTF-8 test kodu hash'i, kanonik JSON hash'i, AST fonksiyon eşlemesi ve sözleşme hash'i kontrollerini yapar. Manifest model, model sürümü, sıcaklık, prompt SHA-256, üretim zamanı ve deneme sayısını tutar.

`backend/services/ifarlab_package_service.py` gelen `result.tar` paketinde path traversal, link, beklenmeyen üye, boyut, JSON ve kimlik uyuşmazlığı kontrolleri uygular; paketin içeriğini çalıştırmaz. Aynı teslim hash'i idempotent işlenir, aynı `run_id` tekrarından yeni kanıt oluşturulmaz.

Eksikler: iki laboratuvarda aynı sözleşme ve şema dosyalarının byte düzeyinde dağıtıldığına dair operasyonel kayıt yoktur; imza/mTLS yoktur; hash bütünlük sağlar ama gönderen kimliği ve inkâr edememezlik sağlamaz.

## Karar motoru

`backend/services/verdict_engine.py` LLM veya `eval` kullanmadan, `Decimal` tabanlı ve izinli operatörlerle karar verir. Eksik zorunlu ölçüm/kanıt, düşük RTF, timeout ve geçersiz ortam `INCONCLUSIVE`; geçerli kural ihlali `FAIL`; tüm kontrollerin geçmesi `PASS` üretir. Assert-robot uyuşmazlığı contradiction olarak saklanır. Gereksinim agregasyonu `STALE > FAIL > NOT_VERIFIED > PASS` önceliğini uygular.

IFARLAB'ın dış kararı bağlayıcı alan olarak, STLC'nin yeniden hesaplaması ise bağımsız kontrol olarak tutulur. Uyuşmazlık `verdict_disagreement` ile işaretlenir; fakat insan incelemesinin atanması, sonuçlandırılması ve supersession kaydı yoktur.

Kritik tutarsızlık: güncel 23 Kasım tasarımı reset hatasını doğrudan `FAIL` ve `sut|infrastructure` olarak tanımlar. Mevcut `verdict_engine.py` ise `reset_failed` durumunu `INCONCLUSIVE` sayar ve `backend/tests/test_verdict_engine.py` bunu doğrular. Bu davranış danışman kararı alınmadan “uyumlu” sayılamaz.

## Kapsam ve raporlama

`backend/services/requirement_coverage_service.py` tam gereksinim setini payda olarak alır ve şu aşamaları ayırır:

`Requirement(version) -> Scenario -> Test Case -> Code SHA-256 -> Execution -> Deterministic Verdict`

Bir koşunun dijital ikiz kanıtı sayılması için explicit `digital_twin` scope, environment ID, twin ID, registry/provenance, kanıt ve deterministik PASS/FAIL gerekir. Local, simulation, mock, rejected, unlinked, stale, missing-evidence ve inconclusive sonuçlar KPI payına girmez. Bu, “test üretildi” ile “gereksinim dijital ikizde doğrulandı” ayrımını doğru kurar.

Depodaki `docs/KPI_3_4_REQUIREMENT_COVERAGE_ENGINE.md`, KPI 3.4 için FR %100 ve NFR %80 hedeflerini tanımlar; görev tanımı belgesinde bu hedefler açık MATISSE kabul ölçütü olarak verilmediğinden danışman/consortium onayı olmadan resmi başarı iddiası yapılmamalıdır.

## Frontend

`frontend/src/components/traceability/TraceabilityDashboard.jsx`, `frontend/src/components/TabPanel.jsx` içindeki Evidence Traceability sekmesine bağlıdır. Ekran:

- FR ve NFR DT executed/verified kartlarını;
- uygulanabilir, uncovered, generated-not-executed, failed/inconclusive ve unclassified sayılarını;
- requirement type, coverage stage ve environment filtrelerini;
- requirement -> scenario -> case -> code -> execution -> verdict drill-down'unu;
- JSON rapor export'unu gösterir.

Eksikler: görev tanımındaki SUT sürüm geçmişi, defect-patch-release zinciri, DEP->PRM->RC ters sorgusu, fiziksel/twin yan yana görünümü, contradiction inceleme kuyruğu ve gerçek twin kamera/kuyruk görünümü bu ASRLab ekranında bulunmaz. Frontend için otomatik component testi yoktur; yalnız üretim derlemesi doğrulanmıştır.

## Doğrulama kanıtı

23 Kasım 2026 tarihinde aşağıdaki yerel doğrulamalar çalıştırılmıştır:

- 61 test: traceability contract, ingestion, verdict engine, requirement-set immutability, coverage, güvenli paket okuma, SUT paketi, yaşam döngüsü modelleri ve gönderim adlandırması.
- 28 test: LLM SUT allowlist, mutasyon motoru/değerlendiricisi/yürütme sınırı, proje yapısı ve bilgi grafı regresyonları.
- Toplam: 89 backend testi geçti.
- `npm run build`: 657 modül dönüştürüldü ve Vite production build geçti. Büyük bundle ve eski Browserslist verisi uyarıları vardır.

Bu testler mock/sentetik veri kullanır. Gerçek IFARLAB twin'i, 16 paralel twin, ROS/MoveIt kanıtı, restricted SSH hesabı, gerçek SUT paketi, fiziksel hücre veya AT-01...AT-08'in tamamı test edilmemiştir.

## Mevcut uygulamanın olgunluk sonucu

ASRLab tarafında sözleşme ve kanıt odaklı bir entegrasyon çekirdeği uygulanmış ve yerel testlerle doğrulanmıştır. Sistem henüz operasyonel dijital ikiz V&V çözümü olarak tamamlanmış değildir. Bir sonraki aşama yeni bir mimari kurmak değil; mevcut çekirdeği IFARLAB'ın kanonik sözleşmeleri ve gerçek kanıt üretimiyle bağlamak, eksik yaşam döngüsü orkestrasyonunu tamamlamak ve çelişkili karar kurallarını onaylatmaktır.
