# ASRLab Sorumlulukları ve Entegrasyonun Uygulama Durumu

## Bölümün amacı ve kapsamı

Bu bölüm, ASRLab tarafından geliştirilen STLC Manager'ın IFARLAB dijital ikiz doğrulama altyapısıyla entegrasyonundaki sorumluluklarını, mevcut uygulama durumunu ve tamamlanması gereken mimari güncellemeleri tanımlar. Temel yaklaşım, mevcut STLC süreçlerini değiştirmek yerine gereksinim, test artefaktı, SUT sürümü, dijital ikiz koşusu, kanıt ve karar arasındaki zinciri değişmez kimlikler ve SHA-256 özetleriyle tamamlamaktır. Üretilmiş bir testin varlığı, testin yürütüldüğü veya bir gereksinimin doğrulandığı anlamına gelmez. Doğrulama iddiası yalnız geçerli yürütme kanıtı ve deterministik karar ile kurulabilir.

## ASRLab sorumlulukları

ASRLab'ın birincil sorumluluğu, IFARLAB tarafından yayımlanan sürümlü SUT paketi ile QCR gereksinimlerini güvenli biçimde içe almak; bu girdilerden izlenebilir test case ve test kodu üretmek; üretim provenance bilgisini kaydetmek; test takımını gereksinim, kabul kriteri, kod kapsamı ve mutasyon açısından değerlendirmek; IFARLAB sonuç paketini içe almak; kararı aynı kural setiyle bağımsız olarak yeniden hesaplamak; gereksinim durumunu SUT sürümü bazında toplamak ve denetlenebilir rapor üretmektir.

ASRLab, SUT gereksinimlerinin sahibi değildir. Belirsiz veya ölçülemez gereksinimler için düzeltme önerisi üretilebilir; ancak QCR içeriği IFARLAB'ın onayı olmadan değiştirilemez. Benzer biçimde, STLC Manager SUT hatası için yama önerisi üretebilir fakat yamayı otomatik uygulamaz. Uygulama ve yeni SUT sürümünün yayımlanması IFARLAB'ın sorumluluğundadır; terfi kararı insan onayına tabidir.

ASRLab, robot kontrolü, Gazebo orkestrasyonu, twin havuzu planlaması, ROS/MoveIt kanıt kaydı, robotik metrik çıkarımı ve fiziksel hücreye yükleme işlevlerini üstlenmez. Bu sorumluluklar IFARLAB'da kalır. ASRLab bu işlevlerin çıktısını sözleşme üzerinden doğrular ve izlenebilirlik zincirine bağlar.

## Mevcut uygulama durumu

STLC Manager'da entegrasyon için çalışan bir çekirdek bulunmaktadır. Sürüm kontrollü gereksinim setleri, submission manifestleri, model ve prompt provenance bilgisi, exact test kodu SHA-256 değeri, gereksinim-test eşlemesi, IFARLAB sonuç teslimleri, deterministik yerel kararlar ve audit olayları ayrı MongoDB koleksiyonlarında saklanmaktadır. Aynı gereksinim seti sürümünün farklı içerikle, aynı SUT sürümünün farklı kaynak özetiyle veya aynı submission revision'ın farklı içerikle yeniden kullanılması uygulama katmanında reddedilmektedir.

SUT paketi içe alma servisi kaynak arşivi, `sut_release.json` ve `requirements.json` üçlüsünü doğrulamakta; arşivi yürütmeden saklamaktadır. QCR tabanlı test gönderiminde her test case'in en az bir gereksinime bağlı olması, inspection testlerinde scenario kimliği bulunması, oracle ve beklenen sonucun QCR kaydıyla aynı olması, validator ve lint sonuçlarının geçmesi ve SUT referansının kayıtlı hash ile eşleşmesi zorunludur.

Sonuçlar authenticated HTTP endpoint veya sınırlı SSH gelen kutusuna bırakılan sonuç paketi üzerinden alınabilmektedir. Paket okuyucu path traversal, symbolic link, beklenmeyen üye, boyut, JSON ve kimlik uyuşmazlığı kontrolleri yapar. Tekrar teslim edilen aynı paket idempotent olarak işlenir; düzeltilmiş teslim özgün kaydın üzerine yazılmaz. IFARLAB'ın kararı bağlayıcı dış karar olarak, STLC Manager'ın yeniden hesapladığı karar ise bağımsız kontrol olarak saklanır; uyuşmazlık ayrıca işaretlenir.

Deterministik karar motoru LLM veya dinamik `eval` kullanmaz. Sayısal karşılaştırmalarda kesin ondalık temsil ve izinli operatörler kullanılır. Eksik zorunlu ölçüm, eksik kanıt, düşük gerçek zaman faktörü ve güvenilmez ortam PASS üretemez. Requirement kapsam servisi functional ve non-functional gereksinimleri ayrı paydalarda değerlendirir; mapped, generated, executable, valid digital-twin executed ve verified aşamalarını birbirinden ayırır. React izlenebilirlik ekranı bu ölçümleri ve requirement'tan yürütme/karara kadar olan zinciri gösterir.

Yerel doğrulamada izlenebilirlik sözleşmesi, paket içe alma, idempotency, karar motoru, kapsam hesaplaması, SUT paket kontrolü, yaşam döngüsü modelleri, LLM SUT allowlist ve mutasyon sınırlarına ilişkin 89 seçili test geçmiştir. Frontend production build de başarıyla tamamlanmıştır. Bu sonuçlar gerçek IFARLAB dijital ikizi veya fiziksel robot ile uçtan uca doğrulama kanıtı değildir.

## Gerekli mimari güncellemeler

Mevcut çekirdeğin üzerine bir doğrulama kampanyası orkestrasyonu eklenmelidir. Kampanya, tek bir SUT sürümü ve requirement set sürümü için test üretimi, gönderim, sonuç, hata, test artefaktı düzeltmesi, yeni SUT sürümü, regresyon ve sürüm adayı aşamalarını aynı kimlik altında yönetmelidir. Her state transition append-only audit olayı üretmeli ve tekrar event işleme idempotent olmalıdır.

Sonuç içe alma sonrasında `fail_cause` alanına göre otomatik fakat kontrollü yönlendirme yapılmalıdır. SUT kaynaklı FAIL tekil hata kaydı açmalı; test artefaktı kaynaklı FAIL test revision ve yeniden üretim işine dönmeli ve SUT hatası oluşturmamalı; infrastructure kaynaklı sonuç IFARLAB incelemesine gitmelidir. Contradiction ve dış/yerel karar uyuşmazlığı insan inceleme kuyruğuna alınmalı, inceleme sonucu ve supersession ilişkisi değişmez biçimde kaydedilmelidir.

Release candidate değerlendirmesi manuel alan gönderimiyle değil, kayıt sistemindeki kanıttan hesaplanmalıdır. Bütün zorunlu QCR durumları, requirement ve acceptance coverage, açık kritik/yüksek hatalar, mutasyon skoru, twin fidelity kaydı, contradiction durumu ve önceki SUT sürümüne göre gerilemeler aynı atomik snapshot içinde değerlendirilmelidir. Snapshot özeti RC raporuna ve insan onaylı terfi kaydına bağlanmalıdır.

MongoDB düzeyinde requirement set version, submission revision, result delivery hash, verdict identity ve lifecycle artefakt kimlikleri için unique indexler kurulmalı ve uygulama başlangıcında doğrulanmalıdır. Uygulama katmanındaki duplicate kontrolleri korunmalı, fakat veritabanı constraintlerinin yerine kullanılmamalıdır. Çok projeli kullanımda geçerli requirement set seçimi `project_id` ve `sut_id` ile sınırlandırılmalıdır.

## ASRLab IFARLAB entegrasyon sözleşmeleri

İki laboratuvar aynı sürümlü contract bundle'ı kullanmalıdır. Bundle; JSON Schema dosyalarını, kimlik biçimlerini, hashing kurallarını, karar kural setini, test case öneklerini ve ortak golden test vektörlerini içermelidir. Contract SHA-256 tam dosya baytları üzerinden hesaplanmalı; JSON yeniden biçimlendirmesi hash'i değiştirdiği için dağıtılan artefakt aynen korunmalıdır. Bütünlük kontrolüne ek olarak üretim ortamında dijital imza veya karşılıklı TLS kullanımı değerlendirilmelidir.

ASRLab'ın beklediği başlıca girişler şunlardır:

- kaynak kod arşivi, `sut_release.json` ve `requirements.json`;
- sürümlü `scenario_catalog.json` ve ground truth;
- `robot_capabilities.json`;
- IFARLAB sonuç paketinde `result.json`, `verdict.json`, `metrics.json`, `junit.xml` ve `coverage.xml`;
- kanıt referansları ve SHA-256 değerleri;
- SUT, twin config, scenario catalog, seed, environment, clock ve verification level provenance bilgileri;
- twin fidelity, deployment ve field finding kayıtları.

ASRLab'ın başlıca çıktıları şunlardır:

- tam ve sürümlü requirement set export'u;
- exact test kodu ve `manifest.json`;
- model, prompt, code-quality ve test mapping provenance bilgisi;
- requirement/test/execution/evidence/verdict matrisi;
- defect ve patch proposal kayıtları;
- regression ve release candidate raporları;
- kapsam, doğrulama ve KPI teknik ölçüm raporları;
- insan inceleme ve terfi karar kayıtları.

Bir sonuç paketinin kabulü, yürütme geçerliliği, robotik değerlendirme, nihai test case kararı, requirement kararı ve teslim durumu ayrı alanlarda tutulmalıdır. Teslim hatası test kararını değiştirmemeli; tekrar teslim yeni test koşusu oluşturmamalıdır.

## Gereksinim doğrulama iş akışı

1. IFARLAB, değişmez SUT sürüm paketini ve tam QCR setini yayımlar.
2. STLC Manager şema ve SHA-256 kontrollerini yapar; requirement set ve SUT sürümünü değişmez kayıt olarak açar.
3. STLC Manager QCR, SUT kaynak kodu, scenario catalog ve robot capability sözleşmesinden test case ve test kodu üretir.
4. Validator, lint ve code-quality kapısı geçilir. Manifestte model, prompt hash, test case, requirement, scenario, oracle ve SUT bilgisi kaydedilir.
5. Test paketi IFARLAB admission kontrolüne gönderilir. Red edilen paket robotik FAIL sayılmaz.
6. IFARLAB her test case'i ayrı run kimliğiyle yürütür; kanıtı test container'ı dışında kaydeder; sim-time metriklerini ve SUT code coverage'ı üretir.
7. IFARLAB ortak karar motoruyla `verdict.json` üretir ve sonuç paketini ASRLab gelen kutusuna teslim eder.
8. STLC Manager paketi güvenli biçimde içe alır, kimlik/hash zincirini doğrular ve kararı aynı rule-set version ile yeniden hesaplar.
9. Requirement durumu SUT sürümü bazında `PASS`, `FAIL`, `NOT_VERIFIED`, `NOT_COVERED` veya `STALE` olarak toplanır. Yalnız SUT kaynaklı FAIL requirement'ı FAIL yapar.
10. Cause routing hata, test revision veya infrastructure incelemesi başlatır. Yeni SUT sürümü tam regresyon kampanyası açar.
11. Bütün çıkış kriterleri kanıtla sağlandığında RC snapshot oluşturulur. İnsan onaylı promotion sonrasında IFARLAB fiziksel doğrulama ve deployment kaydı üretir.

## Kabul kriterleri

ASRLab tarafının entegrasyon kabulü için aşağıdaki koşullar birlikte sağlanmalıdır:

- görev tanımındaki 53 gereksinimin her biri için sahibinin kabul ettiği durum ve kanıt bulunmalıdır;
- AT-01...AT-08 senaryoları ortak ortamda çalıştırılmalı; sentetik testler ayrı raporlanmalıdır;
- aynı contract bundle ve golden vectors iki laboratuvarda aynı kararı üretmelidir;
- aynı submission ve result paketinin tekrarı yeni run, yeni verdict veya duplicate defect oluşturmamalıdır;
- requirement'tan test, SUT, run, evidence ve verdict'e; deployment'tan geriye QCR'ye kadar zincir sorgulanabilmelidir;
- eksik kanıt, ölçülemeyen metrik veya geçersiz ortam hiçbir koşulda PASS üretememelidir;
- test artefaktı ve infrastructure hatası SUT defect'i oluşturmamalıdır;
- onaysız patch uygulanmamalı ve onaysız promotion deployment'a dönüşmemelidir;
- production MongoDB unique indexleri ve restricted SSH hesabı negatif testlerle doğrulanmalıdır;
- frontend requirement gerekçesini ve missing/stale/unlinked halkaları açıkça göstermelidir.

## Danışman onayı gerektiren açık konular

1. Görev tanımında SUT, IFARLAB robot kalite kontrol yazılımı olarak tanımlanırken 23 Kasım tasarımı Gazebo dahil ROS 2 yığınını SUT kapsamına almaktadır. Sınır, coverage ve fail-cause sınıflandırmasını değiştirdiği için tek tanım onaylanmalıdır.
2. 23 Kasım tasarımı reset hatasını doğrudan FAIL saymaktadır. Mevcut STLC karar motoru ve testi `reset_failed` durumunu INCONCLUSIVE saymaktadır. Ortak decision table yayımlanmadan entegrasyon kabul edilmemelidir.
3. RTF 0.7, mutasyon skoru %80, üretim retry sayısı 3 ve hata ayıklama iterasyonu 5 değerlerinin bağlayıcı mı yoksa ölçüm sonrası ayarlanabilir mi olduğu kararlaştırılmalıdır.
4. IFARLAB'ın bağlayıcı verdict'i ile ASRLab yeniden hesabı uyuşmadığında son karar yetkisi, review süresi ve supersession yöntemi tanımlanmalıdır.
5. FR %100 ve NFR %80 değerlerinin resmi MATISSE KPI 3.4 hedefleri olarak kullanılıp kullanılmayacağı onaylanmalıdır.
6. Üretimde SSH inbox'ın tek kanonik teslim yolu olup olmayacağı ve authenticated HTTP endpoint'in hangi amaçla korunacağı belirlenmelidir.
7. Hash kontrolüne ek artifact imzası, mTLS ve role-based approval gereksinimleri güvenlik sorumlularınca karara bağlanmalıdır.

Bu açık kararlar çözülene kadar mevcut sistem “ASRLab entegrasyon çekirdeği uygulanmış ve yerel olarak test edilmiş” olarak raporlanmalı; “uçtan uca dijital ikiz doğrulaması tamamlandı” veya “MATISSE KPI hedefi sağlandı” iddiasında bulunulmamalıdır.
