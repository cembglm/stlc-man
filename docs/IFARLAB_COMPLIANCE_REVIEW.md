# IFARLAB dijital ikiz uyarlaması — uygunluk değerlendirmesi

Bu değerlendirme `ASRLab_STLC_Manager_Uygulama_Gorevleri.md` kabul ölçütleriyle
23 Kasım 2026 tarihindeki kodu karşılaştırır. Mock testler gerçek IFARLAB uçtan
uca testi sayılmaz.

## Mevcut yapı ve yeniden kullanılan parçalar

- MongoDB'de eski `session_history` akışı korunurken gereksinim setleri,
  gönderimler, sonuç teslimleri, kararlar ve olaylar ayrı koleksiyonlarda eklemeli
  olarak tutuluyor.
- Test üretiminde ortak `LLMClient`, sağlayıcı soyutlaması ve model seçimi;
  robot tarafında `robot_capabilities.json`, AST tabanlı validator ve uzak SSH
  çalıştırma yeniden kullanılıyor.
- IFARLAB sonuçları güvenli tar okuma, kimlik/hash bağlantısı ve yerel karar
  motoruyla yeniden hesaplama üzerinden içe alınıyor. IFARLAB kararı
  `authoritative_verdict`, yerel sonuç `stlc_verdict` olarak ayrı tutuluyor;
  fark `verdict_disagreement` ile işaretleniyor.
- React izlenebilirlik ekranı kapsama, doğrulama, matris, kanıt ve karar
  ayrıntılarını gösteriyor. Mutasyon ve gereksinim kapsama çekirdeği mevcut.

## Bu incelemede tamamlanan düzeltmeler

- Yeni SUT paketleri için `QCR-NNN` zorlaması, kaynak arşivi SHA-256 doğrulaması,
  aynı sürüm/farklı hash reddi, `fixes` → hata kaydı bağlantısı ve salt-okunur
  arşiv kaydı eklendi.
- Aynı `requirements_set_version` farklı içerikle tekrar yazılamıyor.
- SUT kodu taşıyan LLM çağrısı, ağ çağrısından önce sağlayıcı ve model bazlı
  `config/llm_sut_allowlist.json` politikasıyla fail-closed denetleniyor. QCR-only
  çağrıların kısıtlanması IFARLAB kararı açık olduğu için şimdilik `false`.
- Hata, yama, sürüm adayı ve terfi modelleri eklendi. RC ölçütlerinden biri
  başarısızsa rapor; açık insan onayı `approved` değilse terfi oluşturulamıyor.
- Yeni izlenebilirlik metadata'sı olan SSH gönderimleri sözleşme dosya adını
  kullanıyor. Metadata'sız eski çağrılar geçiş için `exec-<uuid>.py` yolunda
  kalıyor.
- IFARLAB'a verilecek beş JSON Schema ve test case önek listesi
  `config/ifarlab_schemas/v1/` altında oluşturuldu.

## Yaşam döngüsü ve durum geçişleri

1. IFARLAB kaynak arşivi + `sut_release.json` + `requirements.json` gönderir.
   Hash/şema/kimlik doğrulaması geçerse değişmez SUT sürümü kaydedilir.
2. QCR, senaryo kataloğu ve yetenek sözleşmesinden test üretilir. SUT kaynak
   içeren üretim yalnız izinli yerel sağlayıcı/modelde yapılır.
3. Validator/lint geçerse manifest oluşturulur; oracle alanları QCR'den gelir.
4. `pending → submitted → accepted|rejected → completed|delivery_timeout`.
   SSH exit code bilgi amaçlıdır; bağlayıcı karar gelen `verdict.json`'dır.
5. Her test case ayrı `run_id` ile döner. Yerel motor yeniden hesaplar, farkı
   insan incelemesine yollar; dış kararı değiştirmez.
6. `sut` kaynaklı FAIL hata kaydı açar. `test_artifact` yeniden üretime,
   `infrastructure` IFARLAB bildirimine gider; otomatik tekrar yapılmaz.
7. Yama yalnız öneridir. İnsan onayından sonra IFARLAB uygular ve `fixes`
   bağlantılı yeni SUT sürümü yayınlar; tüm takım regresyon olarak yeniden koşar.
8. Tüm çıkış ölçütleri ve güncel sadakat kaydı sağlanınca RC raporu; ayrıca
   insan onayı verilince terfi kaydı oluşturulur.

## Gereksinim durumu

| Grup | Durum | Kod kanıtı / kalan iş |
|---|---|---|
| INT-01/02 | Kısmen | SUT paket doğrulama ve değişmez kayıt var; operasyonel teslim yolu IFARLAB ile kesinleşmeli. |
| INT-03 | Kısmen | Yerel kontrat/karar motoru ve test vektörleri var; IFARLAB'ın kanonik şema ve motoruyla byte düzeyinde ortaklaştırma bekliyor. |
| INT-04/05 | Kısmen | SSH geçiş yolu, yeni adlandırma ve güvenli gelen kutusu okuyucusu var; gerçek hesap ve iki yönlü E2E yapılmadı. |
| TRC-01/02/03 | Kısmen | Append-only çekirdek, QCR bağlantısı ve bağsız test reddi var; tüm lifecycle koleksiyonlarının DB unique indexleri eklenmeli. |
| TRC-04/05 | Kısmen | Matris/coverage API var; DEP→PRM→RC ters zinciri ve fiziksel kurulum görünümü açık. |
| GEN-01…04/07 | Kısmen | Üretim, validator, manifest ve provenance var; oracle birebir QCR karşılaştırması, katalogda iyi/kusurlu çift zorlaması ve 3 deneme insan kuyruğu tamamlanmalı. |
| GEN-05/06 | Kısmen | Kapsama ve mutasyon modülleri var; SUT dili/aracı ve IFARLAB mutant sürüm biçimi açık. |
| VRD-01/02/03/04 | Kısmen | Deterministik motor, öncelik ve uyuşmazlık kaydı var; STALE girdilerinin tamamı ve `fail_cause` bazlı gereksinim agregasyonu tamamlanmalı. |
| VRD-05 | Kısmen | Contradiction kaydı var; insan inceleme sonucu workflow'u açık. |
| FIX-01/02/05/06 | Kısmen | Şemalı hata/yama ve onay kapısı var; otomatik sınıflandırma, test sürüm artırımı ve 5 iterasyon kuyruğu açık. |
| FIX-04 | Açık | Yeni SUT geldiğinde bütün takımın otomatik regresyon planlanması ve gerileme raporu yok. |
| REL-01/02/03 | Kısmen | RC/terfi kapıları model ve API düzeyinde var; ölçütleri veri tabanından otomatik hesaplayan orkestrasyon açık. |
| MON-02 | Kısmen | Kapsama/karar matrisi var; tam takım süresi, iterasyon ve gerilemeler tek raporda tamamlanmalı. |
| MON-03/REL-05 | Açık | Saha bulgusu → test adayı ve sapma/geri alma kayıt akışı yok. |
| NFR-03 | Kısmen | Hash, güvenli tar ve API auth var; Windows hesap izolasyonu sahada doğrulanmalı. |
| NFR-04 | Karşılandı (kod) | İzin listesi çağrı katmanında, ağ I/O öncesinde zorlanıyor; üretim onay listesini IFARLAB imzalamalı. |

## Windows OpenSSH gelen kutusu prosedürü

Bu adımlar yönetici yetkisi ve güvenlik duvarı değişikliği gerektirdiğinden
kullanıcı onayı alınmadan çalıştırılmaz.

1. `Get-WindowsCapability -Online | ? Name -like 'OpenSSH.Server*'` ile durumu
   kontrol et; gerekiyorsa `Add-WindowsCapability` ile sunucuyu kur.
2. `sshd` hizmetini otomatik başlatmaya ayarla ve yalnız IFARLAB ağına izin veren
   inbound TCP/22 güvenlik duvarı kuralı oluştur.
3. Etkileşimli oturum yetkisi olmayan ayrı bir yerel hesap ve yalnız ona yazma
   ACL'i bulunan `C:\ProgramData\STLC\ifarlab_inbox` dizini oluştur.
4. `authorized_keys` satırında `restrict,from="192.168.3.10"` ve IFARLAB public
   key kullan; özel anahtar hiçbir zaman ASRLab'a kopyalanmaz.
5. `IFARLAB_INBOX_DIR` değerini bu dizine ayarla. Uygulama hesabına sadece okuma,
   teslim hesabına sadece oluşturma/yazma hakkı ver.
6. IFARLAB hesabıyla gelen kutusuna dosya yazılabildiğini; üst dizine, uygulama
   kaynaklarına ve başka kullanıcı dizinlerine yazılamadığını negatif testlerle
   doğrula.
7. Geçerli, bozuk hash, tekrar `run_id`, red ve zaman aşımı paketlerini birlikte
   test et; bu testleri mock sonuçlarından ayrı raporla.

## Açık dış kararlar ve riskler

- SUT dili, mutasyon aracı, mutant sürüm adlandırması, paket teslim kanalı,
  `result.json` tam şeması ve gelen kutusu üretim yolu IFARLAB ile kararlaştırılmalı.
- Yerel model varsayılan tek izinli sınıftır; dosyadaki geçici yerel onay üretimde
  IFARLAB tarafından adlandırılmış model ve gerçek onay zamanı ile değiştirilmelidir.
- Öneri eşikleri (3 yeniden üretim, 5 iterasyon, %80 mutasyon) yapılandırılabilir
  hale getirilip ortak kabul testinde sabitlenmelidir.
- Gerçek ikiz/robot, SSH hesabı ve güvenlik duvarı bu çalışma sırasında erişilebilir
  değildi; dolayısıyla AT-01…AT-08 gerçek E2E olarak geçti denemez.
