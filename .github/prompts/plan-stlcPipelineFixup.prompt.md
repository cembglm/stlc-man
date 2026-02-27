# Plan: STLC Pipeline Çalışır Hale Getirme

**TL;DR:** Pipeline şu an yarım kalmış — 11 modülden sadece 5-6'sı `handleStartPipeline`'da gerçekten çalışıyor, sıralama garanti değil, bağımlılık kontrolü yok ve backend pipeline kodu ölü. Frontend orchestration yaklaşımıyla (mevcut modül endpointleri üzerinden) tüm 11 modülü pipeline'da çalıştırılabilir hale getireceğiz. MongoDB `session_history` üzerinden modüller arası veri akışı korunacak.

## Mevcut Sorunlar
- **Sıralama hatası:** `Set` insertion order kullanılıyor, STLC sırası garanti değil
- **6 modül pipeline'da çalışmıyor:** `test-case-generation`, `test-case-optimization`, `test-execution`, `test-reporting`, `test-closure` sadece kendi formlarının `handleRun` callback'i ile çalışıyor — `handleStartPipeline` bunlara erişemiyor
- **Bağımlılık kontrolü yok:** Kullanıcı Test Case Gen seçip Test Scenario Gen seçmezse uyarı bile çıkmıyor
- **`validatePipeline()` hiç çağrılmıyor**
- **Backend `pipeline/` paketi ölü kod:** Hiçbir route'a bağlı değil

---

## Steps

### 1. Modül Bağımlılık Haritası Oluştur
- [frontend/src/data/processes.js](frontend/src/data/processes.js) dosyasına her modül için `dependencies` alanı ekle
  - Örnek: `test-case-generation` → `dependencies: ['test-scenario-generation']`
  - `test-case-optimization` → `['test-case-generation']`
  - `test-code-generation` → `['test-case-optimization', 'environment-setup']`
  - `test-execution` → `['test-code-generation']`
  - `test-reporting` → `['test-execution']` (veya tüm önceki süreçler)
  - `test-closure` → `['test-reporting']`
  - `test-planning` → `['code-review', 'requirement-analysis']`
  - `test-scenario-generation` → `['test-planning']`
  - `code-review`, `requirement-analysis`, `environment-setup` → `[]` (bağımsız)

### 2. Bağımlılık Uyarı Sistemi Ekle
- [frontend/src/App.jsx](frontend/src/App.jsx) içindeki `handleStartPipeline` fonksiyonuna (satır ~678) bağımlılık kontrol mantığı ekle
- Seçilen modüllerin `dependencies` alanına bak → seçilmemiş bağımlılıklar varsa kullanıcıya uyarı göster (modal veya toast)
- Uyarıya rağmen kullanıcı devam edebilsin (engelleme yapılmayacak)
- [frontend/src/components/TabPanel.jsx](frontend/src/components/TabPanel.jsx) Pipeline tab'ına uyarı banner ekle — seçilen modüllerin eksik bağımlılıkları varsa sarı uyarı göster

### 3. Pipeline Sıralama Düzeltmesi
- [frontend/src/App.jsx](frontend/src/App.jsx) `handleStartPipeline` içinde `Array.from(selectedProcesses)` yerine `processes` dizisindeki index sırasına göre sırala:
  ```js
  const orderedProcessIds = processes
    .filter(p => selectedProcesses.has(p.id))
    .map(p => p.id);
  ```
- Bu, modüllerin her zaman STLC yaşam döngüsü sırasında çalışmasını garanti eder

### 4. Tüm 11 Modülü Pipeline'da Çalıştırılabilir Hale Getir
Bu en kritik adım. İki kategori modül var:

**A) Redux-tabanlı modüller** (zaten çalışıyor — küçük düzeltmelerle):
- `code-review`, `requirement-analysis`, `test-planning`, `environment-setup`: [App.jsx](frontend/src/App.jsx) `handleProcessRun` içinde Redux dispatch ile çalışıyor. Pipeline'da dosya eşlemeleri ve konfigürasyon aktarımını düzelt.

**B) Form state callback modülleri** (pipeline'da çalışmıyor — ana çalışma):
- `test-case-generation`, `test-case-optimization`, `test-execution`, `test-reporting`, `test-closure`: Bunlar kendi form bileşenlerinin `handleRun` callback'i ile çalışıyor.

**Çözüm yaklaşımı:** Pipeline orchestration'ı [TabPanel.jsx](frontend/src/components/TabPanel.jsx) içine taşı, çünkü form state'leri (`testCaseFormState`, `testCaseOptimizationFormState`, vb.) zaten orada tutuluyor.

- [frontend/src/components/TabPanel.jsx](frontend/src/components/TabPanel.jsx) içine `executePipelineStep(processId)` fonksiyonu ekle:
  - Redux-tabanlı modüller için → `onRun(processId, files)` çağır (App.jsx'e delege et)
  - `test-scenario-generation` için → `testScenarioFormState.handleRun()` çağır
  - `test-case-generation` için → `testCaseFormState.handleRun()` çağır
  - `test-case-optimization` için → `testCaseOptimizationFormState.handleRun()` çağır
  - `test-code-generation` için → `onRun(processId)` çağır (window.testCodeGenerationExecute pattern)
  - `test-execution` için → `testExecutionFormState.handleRun()` çağır
  - `test-reporting` için → `testReportingFormState.handleRun()` çağır
  - `test-closure` için → `testClosureFormState.handleRun()` çağır

- `runPipeline()` fonksiyonu TabPanel'de: sıralı modülleri iterate et, her adım için `executePipelineStep` çağır, tamamlanma sinyalini bekle, sonra bir sonrakine geç

- Her form bileşeninin pipeline mode'da **otomatik konfigüre** olması için:
  - `pipelineMode={true}` prop'unu form'lar zaten alıyor
  - Pipeline config'den (usePipelineConfig hook'undaki `getProcessConfig`) alınan ayarları form'a prop olarak geç
  - Form'ların pipeline mode'da UI etkileşimi beklemeden doğrudan çalışabilmesi için `autoRun` veya benzer bir mekanizma

### 5. Pipeline Tamamlanma Takibi
- Her form bileşenine `onPipelineStepComplete(processId, result)` callback'i ekle
- Form kendi çalışmasını bitirdiğinde bu callback'i çağırsın
- TabPanel bu callback ile bir sonraki adıma geçsin
- `pipelineStatus` state'ini her adımda güncelle: `pending` → `running` → `completed` / `error`
- Pipeline hata durumunda durma veya devam etme seçeneği sun

### 6. Pipeline Konfigürasyonunun Doğru Aktarılması
- [frontend/src/hooks/usePipelineConfig.js](frontend/src/hooks/usePipelineConfig.js) `getBackendConfig()` fonksiyonu mevcut ama hiç kullanılmıyor — pipeline başlatılırken her modülün config'ini bu fonksiyonla al ve ilgili API çağrısına aktar
- GlobalAIConfig'den gelen model/temperature ayarlarının her modüle doğru uygulandığından emin ol

### 7. `validatePipeline()` Bağlantısı
- [App.jsx](frontend/src/App.jsx) ~satır 293'teki `validatePipeline()` fonksiyonunu pipeline başlamadan önce çağır
- Eksik dosya eşlemeleri varsa kullanıcıyı uyar (engelleme yapma, sadece uyarı)

### 8. Backend Ölü Kod Temizliği
- [backend/pipeline/pipeline_controller.py](backend/pipeline/pipeline_controller.py): Kullanılmıyor — sil veya ileride kullanılmak üzere yorum ekle
- [backend/pipeline/pipeline_executor.py](backend/pipeline/pipeline_executor.py): Kullanılmıyor — sil veya yorum ekle
- Backend'de yeni route eklemeye **gerek yok** — mevcut modül endpointleri yeterli

### 9. Frontend Ölü Kod Temizliği
- [frontend/src/components/Pipeline.jsx](frontend/src/components/Pipeline.jsx): Hiçbir yerde kullanılmıyor — sil
- [frontend/src/components/PipelineView.jsx](frontend/src/components/PipelineView.jsx): Hiçbir yerde kullanılmıyor — sil

### 10. Session ID Tutarlılığı
- Pipeline boyunca **aynı `sessionId`** kullanıldığından emin ol — tüm modüller aynı `session_history` dokümanına yazar ve okur
- MongoDB üzerindeki `session_history.processes` altında her modülün çıktısı saklanır → sonraki modül `session_id` ile sorgulayarak önceki çıktıyı alır (mevcut pattern korunacak)

---

## Verification
1. Tüm 11 modülü pipeline'da seç → "Start Pipeline" tıkla → sırayla çalışmasını doğrula
2. Sadece ortadaki modülleri seç (örn. Test Case Gen + Test Code Gen) → bağımlılık uyarısı göründüğünü doğrula → devam et → çalışmasını kontrol et
3. Herhangi bir modül hata verirse pipeline'ın doğru şekilde durduğunu ve hata status'ünün göründüğünü doğrula
4. MongoDB `session_history`'de tüm modül çıktılarının `session_id` altında doğru kaydedildiğini kontrol et
5. Pipeline sonlandıktan sonra her modülün output panelinde sonuçlarının göründüğünü doğrula

## Decisions
- **Frontend orchestration** tercih edildi (backend pipeline endpoint'i yok) — mevcut modül API'leri kullanılacak
- **Pipeline orchestration TabPanel.jsx'e taşınacak** — form state callback'lerine erişim için gerekli (App.jsx'ten erişilemiyor)
- **Bağımlılık kontrolü uyarı modunda** — eksik bağımlılıklarda engelleme yok, sadece bilgilendirme
- **MongoDB session_history** mekanizması korunacak — modüller arası veri akışı `session_id` üzerinden
