# ASRLab STLC Manager Uygunluk ve Geliştirme Raporu

**Tarih:** 24 Kasım 2026  
**Kapsam:** `ASRLab_STLC_Manager_Uygulama_Gorevleri.md` içindeki A0-A11 işleri  
**İncelenen sürüm:** yerel depo, başlangıç commit'i `79b4138`

## Yönetici özeti

STLC Manager'da izlenebilirlik, karar motoru, SSH tabanlı gönderim, LLM kaynak kodu izin kapısı, mutasyon altyapısı ve kapsam raporlaması için çalışan bir çekirdek vardı. Buna rağmen 24 Kasım isterleriyle tam uyumlu değildi. Özellikle QCR önceliği zorunlu değildi, reset hatası yanlış sınıflanabiliyordu, aynı `run_id` farklı içerikle yeniden kabul edilebiliyordu, izlenebilirlik koleksiyonlarının unique indeksleri başlangıçta kurulmadı, HTTP sonuç alımı varsayılan olarak açıktı, ertelenmiş `scenario_id` alanı hareket testlerinin kapsam zincirini kesiyordu ve uygun olmayan bir sürüm adayı için rapor üretilemiyordu.

Bu çalışma kritik sözleşme ve güvenlik farklarını kapattı. QCR modeli sıkılaştırıldı; reset, RTF ve `fail_cause` davranışı hizalandı; sonuç yönlendirme ve insan inceleme kuyruğu eklendi; indeksler başlangıç kapısına bağlandı; kapsam ve sürüm adayı kapıları ayrıştırıldı; yeni SUT sürümü için regresyon kampanyası kuyruğu eklendi; ters sorgular ve arayüz filtreleri genişletildi. Simülasyon aşamasında sadakat kaydı kapsam dışı olduğu için sistem bilinçli olarak hiçbir sürümü tam aday ilan etmez.

Tam uyum henüz ilan edilemez. IFARLAB'ın sürümlü sözleşme paketi ve resmi karar vektörleri depoda yoktur; gerçek sonuç paketiyle uçtan uca test yapılmamıştır; yapılandırma mutantlarının `mutant_request.json` üzerinden SSH ile yürütülmesi tamamlanmamıştır; Windows OpenSSH Server ve kısıtlı gelen kutusu hesabı yönetici onayı gerektirir.

## A0 Mevcut durum doğrulaması

| Alan | Önceki durum | Doğrulanan durum | Sonuç |
|---|---|---|---|
| Gereksinim modeli | Sürümlü set ve SHA kaydı var | QCR önceliği ve QCR kimlik kuralları eksikti | Düzeltildi |
| Test üretimi | Çoklu sağlayıcı ve üretim kaydı var | SUT kaynak kodu için çağrı katmanı izin kapısı var | Uygun |
| Robot yetenekleri | `robot_capabilities.json` ve AST doğrulama var | Gönderim öncesi kapı çalışıyor | Uygun |
| IFARLAB aktarımı | SSH gönderimi ve eski geçiş yolu var | Sonuç için SSH inbox paketi var; HTTP yolu açıktı | HTTP varsayılan kapatıldı |
| Karar motoru | Deterministik yeniden hesaplama var | Reset hatası eski kurala göre INCONCLUSIVE olabiliyordu | Düzeltildi |
| Rapor ve arayüz | Kapsam paneli ve izlenebilirlik zinciri var | SUT sürümü ve doğrulama seviyesi filtreleri yoktu | Eklendi |

## A1 Sözleşme uyumu

**Durum: Kısmi, dış paket bekliyor.** Yerel sözleşme 1.2 olarak QCR kimlikleri, `mandatory` ve `desired` öncelikleri, doğrulama seviyeleri ve adlandırma kurallarıyla güncellendi. Karar motorunda reset `failed` sonucu `FAIL/sut`, `stack_down` ve `timeout` sonuçları `FAIL/infrastructure` olur. Test sırasında altyapı veya twin çökmesi INCONCLUSIVE kalır. RTF alt sınırı 0,7'dir.

IFARLAB'ın kanonik sözleşme paketi ve resmi test vektörleri bulunmadığı için birebir `verdict.json` eşitliği kanıtlanamadı. Yerel sözleşme IFARLAB kaynağının yerine geçirilmedi; bu kalem entegrasyon öncesi blokerdir.

## A2 QCR önceliği

**Durum: Tamamlandı.** `QCR-NNN` kayıtlarında `priority` zorunludur ve yalnız `mandatory` veya `desired` olabilir. `QCR-YYYY-MM-DD` setleri yalnız QCR kimliği kabul eder. Üretim raporu testsiz zorunlu QCR'leri ayrı listeler. Sürüm adayı kapısı yalnız bütün zorunlu QCR'ler PASS olduğunda bu kriteri geçirir; istenen QCR'ler raporda kalır fakat kapıyı bloke etmez.

## A3 Oranlar

**Durum: Tamamlandı.** Fonksiyonel ve fonksiyonel olmayan kapsam ile doğrulama ayrı paydalarda hesaplanır. Toplam kapsam, toplam doğrulama ve kabul kriteri kapsaması ayrıca verilir. Yüzde 100 fonksiyonel ve yüzde 80 fonksiyonel olmayan hedefleri rapor hedefidir; karar kuralına katılmaz. `all_requirements_met` yalnız iki hedef de sağlanırsa doğrudur. Sürüm adayı çıkış kapısı bundan ayrı tutulur.

## A4 Teklik ve tekrar güvenliği

**Durum: Tamamlandı.** Uygulama başlangıcında gereksinim seti sürümü, `submission_id`, `run_id`, teslim SHA-256 değeri, karar kimliği, hata, yama, sürüm adayı, terfi, inceleme ve regresyon kampanyası kimlikleri için unique indeksler kurulur. Aynı teslim hash'i idempotent replay olarak döner. Aynı `run_id` farklı içerikle gelirse çatışma hatası oluşur ve ikinci sonuç yazılmaz.

## A5 Sonuç yönlendirme ve inceleme

**Durum: Tamamlandı.** Bağlayıcı IFARLAB kararı `FAIL/sut` ise hata kaydı, `test_artifact` ise sürüm artışı gereken yeniden üretim işi, `infrastructure` ise IFARLAB bildirim işi oluşturulur. Yönlendirme olayları teslim kaydına outbox olarak gömülür ve yeniden alımda idempotent olarak maddileştirilir. Çelişki veya yeniden hesaplama uyuşmazlığı insan inceleme kuyruğuna girer; bağlayıcı kaynak IFARLAB olarak korunur. Yama ve terfi kayıtlarında mevcut insan onayı kapıları korunmuştur.

## A6 Regresyon kampanyası

**Durum: Temel akış tamamlandı.** Yeni SUT sürümü içe alındığında aynı gereksinim setindeki en güncel test gönderimleri yeni `submission_id` ve yeni SUT `version`, `commit`, `source_sha256` referansıyla kopyalanır. Kod değişmeden kalır ve gönderimler normal validator ile SSH dispatch kapısında kuyruğa alınır. Gerileme listesinin önceki PASS ile yeni FAIL'i karşılaştıran ayrı rapor görünümü henüz tamamlanmamıştır.

## A7 Mutasyon

**Durum: Kısmi.** Mevcut mutasyon motoru seed, seçilebilir mutantlar, temel koşu doğrulaması, öldürülen ve hayatta kalan sınıflandırması ve öldürülen bölü toplam skorunu sağlar. Mutasyon sonuçları gereksinim kararı sayılmaz. Ancak geçerli SUT için yapılandırma mutantları, resmi `mutant_request.json` ve `mutant_result.json` sözleşmeleri, SSH aktarımı ve hayatta kalan mutantlardan otomatik ek test önerisi tamamlanmamıştır.

## A8 Sürüm adayı ve terfi

**Durum: Kısmi.** RC raporu başarısız kriterleri gizlemeden üretilebilir ve `eligible` alanı yanlış kalır. Sadakat kaydı bulunmadığı için simülasyon aşamasında RC uygunluğu her zaman yanlıştır. Terfi yalnız uygun RC ve açık insan onayıyla kaydedilir. Tüm kriterlerin tek MongoDB snapshot veya transaction üzerinden hesaplandığı birleşik RC üretim servisi henüz yoktur.

## A9 Ters sorgular ve arayüz

**Durum: Büyük ölçüde tamamlandı.** Yeni ters sorgu uç noktası gereksinim-test-SUT matrisi, bir QCR'yi doğrulayan testler, sürüm bazında FAIL gereksinimler, hata-yama-sürüm zincirleri ve terfi-RC-gereksinim zincirlerini döndürür. Eksik SUT veya koşu bağlantıları `broken_links` altında görünür. Arayüzde SUT sürümü, doğrulama seviyesi ve DT ortamı filtreleri ile zorunlu QCR ve sadakat kapıları gösterilir. Açık hatalar ve gerilemeler için ayrı üst düzey ekran geliştirmesi kalmıştır.

## A10 SSH gelen kutusu

**Durum: Yazılım kapısı tamamlandı, sistem kurulumu bekliyor.** Sonuçların HTTP ile alınması varsayılan olarak kapalıdır ve yalnız `ALLOW_HTTP_RESULT_INGEST=true` ile yerel geliştirmede açılabilir. SSH inbox paket okuyucusu arşiv geçişi, dosya listesi ve sözleşme doğrulaması yapar. PC1 üzerinde OpenSSH Server kurulumu, kısıtlı hesap, `authorized_keys` içindeki `restrict,from="192.168.3.10"` kuralı ve gerçek anahtar değişimi yönetici onayı olmadan yapılmadı.

## A11 Test ve teslim raporu

### Otomatik doğrulama

- Python derleme kontrolü: başarılı.
- Kritik çevrimdışı test paketi: 69 test başarılı.
- SUT paketi ve regresyon kampanyası modülü: 5 test başarılı; ana pakette de yer alır.
- React üretim derlemesi: başarılı, 657 modül dönüştürüldü.
- Tam backend test toplaması: 162 test bulundu.
- Tam paket koşusu: `test_external_api`, monitoring ve bazı uzak yürütme testleri bu makinede harici servis veya event-loop beklemesine girdi; assertion hatası raporlanmadan süre sınırında durduruldu. Bu gruplar başarı olarak sayılmadı.

### Gerçek IFARLAB sonuçları

Gerçek IFARLAB sonuç paketi alınmadı. Gerçek twin koşusu, gerçek SSH dönüşü, gerçek kanıt SHA doğrulaması ve resmi vektör uyumu doğrulanmış kabul edilmez.

### Sentetik ve birim test sonuçları

Sentetik sonuçlarla PASS, SUT kaynaklı FAIL, test artifact yönlendirmesi, altyapı reset hatası, RTF kaynaklı INCONCLUSIVE, uyuşmazlık incelemesi, aynı teslim replay'i ve aynı `run_id` çatışması doğrulandı. Bu sonuçlar gerçek uçtan uca test değildir.

## Değişen dosya grupları

- Sözleşme ve modeller: `backend/models/traceability.py`, `backend/models/ifarlab_lifecycle.py`, `config/ifarlab_contract_v1.json`
- Karar ve izlenebilirlik: `backend/services/verdict_engine.py`, `backend/services/traceability_service.py`, `backend/services/requirement_coverage_service.py`
- Yaşam döngüsü ve SUT: `backend/services/lifecycle_service.py`, `backend/services/sut_package_service.py`
- Güvenlik ve altyapı: `backend/core/database.py`, `backend/core/settings.py`, `backend/app.py`, `backend/routers/traceability_router.py`
- Arayüz: `frontend/src/components/traceability/TraceabilityDashboard.jsx`
- Testler: ilgili `backend/tests/test_*` dosyaları

## Commit durumu

Değişiklikler çalışma ağacında bırakıldı ve otomatik commit oluşturulmadı. Depoda önceden bulunan izlenmeyen `docs/ifar_lab_review/` içeriğine dokunulmadı. İnceleme sonrasında A1-A11 gruplarına göre ayrık commit'ler oluşturulabilir.

## Canlı entegrasyon öncesi zorunlu adımlar

1. IFARLAB'ın kanonik sözleşme paketini ve resmi vektörlerini içe alın; yerel motoru birebir çıktı eşitliğiyle doğrulayın.
2. PC1 OpenSSH Server ve kısıtlı inbox hesabı için yönetici onayı verin; gerçek anahtarlarla negatif dizin yazma testi yapın.
3. Gerçek bir gönderim ve her test case için ayrı sonuç paketiyle uçtan uca kabul testi yapın.
4. Yapılandırma mutantı SSH akışını ve resmi mutant şemalarını tamamlayın.
5. Gerileme görünümünü ve tek-snapshot RC hesaplama servisini tamamlayın.
