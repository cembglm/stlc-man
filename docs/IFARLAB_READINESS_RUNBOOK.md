# IFARLAB entegrasyon hazırlık runbook'u

Bu belge yalnızca ASRLab tarafındaki hazırlığı ve dış bağımlılıkları ayırır. İnsan veya IFARLAB onayı yerine geçmez.

## Otomatik ön kontrol

Depo kökünde çalıştırın:

```powershell
python scripts/ifarlab_preflight.py
```

Çıkış kodu `0` ortak akışın hazır olduğunu, `2` ise en az bir yerel hata veya dış blokaj bulunduğunu gösterir. Aynı rapor kimlik doğrulamalı API üzerinden `GET /api/integrations/ifarlab/v1/readiness` adresindedir.

## Kanonik sözleşme paketi

IFARLAB'dan alınan `ifarlab-stlc-contracts-1.2.0.tar` dosyasını varsayılan olarak `config/ifarlab_contracts/` altına koyun. Doğrulayıcı:

- paket SHA-256 değerini sabitlenmiş IFARLAB değeriyle karşılaştırır;
- tar path traversal ve link girişlerini reddeder;
- paket içindeki `SHA256SUMS` dosyasını doğrular;
- motor, rule set, README, changelog, paket manifesti, şema ve vektör varlığını denetler.

Paket doğrulanmadan yerel motor sürümünü `2.6.0` olarak değiştirmeyin.
Paket README'sindeki kanonik vektör komutu 53 başarılı ve 0 başarısız sonuç vermelidir. Sonuç, paket SHA-256 değeriyle birlikte `config/ifarlab_contracts/validation_result.json` dosyasına kaydedilmeden preflight ortak uyumu hazır saymaz.

## SSH-only sonuç teslimi

- `ALLOW_HTTP_RESULT_INGEST=false` kalmalıdır.
- IFARLAB'ın host, port, kullanıcı, inbox dizini ve host-key fingerprint bilgileri alınmalıdır.
- ASRLab kimlik dosyası `SSH_EXECUTION_IDENTITY_FILE` ile yapılandırılmalıdır.
- Gelen paketler yalnızca `IFARLAB_INBOX_DIR` altından içe alınır.
- İlk aktarımda host key elle doğrulanıp sabitlenmelidir; otomatik `StrictHostKeyChecking=no` kullanılmamalıdır.

## İnsan kararları

Aşağıdakiler otomatik olarak onaylanmaz:

- `robot_capabilities.json` ve Q1–Q5 davranışları;
- LLM provider/model onayı;
- çelişkili verdict incelemesi;
- RC/promosyon kararı.

İnceleme sonucu özgün verdict'i değiştirmez. `/reviews/{review_id}/decisions` yeni, izlenebilir bir superseding verdict oluşturur.

Ortak kararların tek makine-okunabilir listesi `config/ifarlab_decisions.json` dosyasındadır. Bir karar yalnızca gerçek dış onay alındıktan ve kanıtı kaydedildikten sonra `approved` yapılmalıdır.
