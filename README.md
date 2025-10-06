# STLC Manager

Bu proje, **Software Testing Life Cycle (STLC)** adımlarını yönetmek ve otomasyonunu sağlamak amacıyla oluşturulmuş bir Full Stack uygulamasıdır.  

**STLC** aşağıdaki 11 modülü içerir:

1. **Code Review** - Kod kalitesi analizi ve öneriler
2. **Requirement Analysis** - Gereksinim doküm## 🚀 Önemli Geliştirmeler & Optimizasyonlar

### ✅ Gemini API Optimizasyonları
- **Finish reason handling** - Enum değerlerinin doğru işlenmesi
- **Timeout management** - 300s timeout ile stabilite artışı
- **Error recovery** - Otomatik retry mekanizmaları
- **Response validation** - Güvenli text extraction

### ✅ MongoDB Session Management
- **Complete tracking** - Tüm STLC işlemlerinin kayıt altına alınması
- **Analytics support** - Performans metrikleri ve istatistikler
- **Session restoration** - İşlem geçmişinin geri getirilebilmesi
- **Data structure** - Nested JSON format ile organize veri

### ✅ Multi-Model Support
- **7+ Model Integration** - CodeLlama, Kimi-Dev, GPT-OSS, DeepSeek vs.
- **Intelligent fallback** - Model timeout durumunda otomatik geçiş
- **Performance optimization** - Response time tracking ve optimizasyon
- **Success rate monitoring** - Model başarı oranlarının takibi

### ✅ Token Management System
- **Intelligent chunking** - Büyük dosyaların akıllı bölünmesi
- **Context preservation** - Chunk'lar arası bağlamın korunması
- **Memory optimization** - Efficient text processing
- **Size validation** - Otomatik dosya boyutu kontrolü

## 📊 Performans Metrikleri

### Response Times (Average)
- **Code Review**: 8-15 saniye
- **Requirement Analysis**: 12-20 saniye  
- **Test Planning**: 10-18 saniye
- **Test Scenario Generation**: 15-25 saniye
- **Test Case Optimization**: 14-103 saniye (model bağımlı)

### Success Rates
- **Gemini Pro**: %95+ (timeout optimizasyonları sonrası)
- **LM Studio**: %90+ (local model stabilitesi)
- **OpenAI**: %98+ (en stabil)

## 🔐 Güvenlik & En İyi Uygulamalar

- **Environment variables** - Sensitive data için .env kullanımı
- **Input validation** - Tüm user input'ların doğrulanması
- **Error handling** - Comprehensive exception management
- **Rate limiting** - API çağrılarının optimize edilmesi
- **Data sanitization** - File upload güvenlik kontrolleri

## 🤝 Katkıda Bulunma

### Yeni Modül Ekleme
1. `backend/stlc/` klasörüne yeni `.py` dosyası ekleyin
2. `run_step(input_data)` fonksiyonunu implement edin
3. MongoDB integration için database kayıt fonksiyonlarını ekleyin
4. Frontend'e yeni modül için UI bileşeni ekleyin

### Model Entegrasyonu
1. `backend/core/model_client.py`'de `get_model_identifier()` metodunu güncelleyin
2. Yeni model için test case'ler ekleyin (`tests/unit/`)
3. Performance benchmark'ları çalıştırın
4. Documentation'ı güncelleyin

### Test Contribution
- Unit tests: `tests/unit/` klasörüne ekleyin
- Integration tests: `tests/integration/` klasörüne ekleyin
- Performance tests: `tests/performance/` klasörüne ekleyin

Pull Request'ler, bug raporları ve feature request'ler memnuniyetle karşılanır!ı analizi  
3. **Test Planning** - Test planı oluşturma ve zamanlama
4. **Test Scenario Generation** - Kapsamlı test senaryoları üretimi
5. **Test Case Generation** - Test case'lerin oluşturulması
6. **Test Case Optimization** - Test case'lerin optimizasyonu
7. **Test Code Generation** - Otomatik test kodu üretimi
8. **Environment Setup** - Test ortamı kurulum rehberi
9. **Test Execution** - Test yürütme
10. **Test Reporting** - Test raporlama
11. **Test Closure** - Test sürecinin kapatılması

Her modül tek başına veya **pipeline** olarak çalıştırılabilir ve **MongoDB** üzerinde merkezi prompt yönetimi sunar.

## 🚀 Hızlı Başlangıç

### Ön Gereksinimler
- **Python 3.8+**
- **Node.js 16+** 
- **MongoDB** (Yerel kurulum veya MongoDB Atlas)
- **Git**

### 1. Projeyi İndirin
```bash
git clone https://github.com/YOUR_USERNAME/STLC-Manager.git
cd STLC-Manager
```

### 2. MongoDB'yi Başlatın
```bash
# Yerel MongoDB
mongod

# Veya Docker ile
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 3. Backend Kurulumu
```bash
cd backend
pip install -r requirements.txt

# Base prompt'ları otomatik yükle (opsiyonel - uygulama başlatıldığında otomatik yapılır)
python ../setup_prompts.py

# Backend'i başlat
python app.py
```

### 4. Frontend Kurulumu
```bash
cd frontend
npm install
npm run dev
```

### 5. Uygulamayı Açın
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## ✨ Özellikler

### 🤖 Otomatik Prompt İnisializasyonu
- GitHub'dan projeyi indirip ilk kez çalıştırdığınızda **tüm modüller için base prompt'lar otomatik olarak database'e eklenir**
- Her modül kendi default prompt'ları ile gelir
- Prompt'lar MongoDB'de merkezi olarak yönetilir

### 📝 STLC Modülleri ve Özellikleri

| # | Modül | Açıklama | Çıktı Formatı | AI Model | Otomatik Prompt |
|---|-------|----------|---------------|----------|-----------------|
| 1 | **Code Review** | Kod kalitesi, güvenlik, performans analizi | JSON + Detaylı rapor | Multi-model | ✅ ISTQB standartları |
| 2 | **Requirement Analysis** | Gereksinim uyumluluk ve eksiklik kontrolü | Structured JSON | Gemini Pro | ✅ IEEE standartları |
| 3 | **Test Planning** | Gantt chart, zaman çizelgesi ve kaynak planı | JSON + Timeline | GPT/Gemini | ✅ PMI metodolojisi |
| 4 | **Test Scenario Generation** | Comprehensive test senaryoları ve edge case'ler | JSON Array | Multi-model | ✅ ISTQB sertifikalı |
| 5 | **Test Case Generation** | Detaylı test case'ler ve adımları | Structured JSON | CodeLlama | ✅ IEEE 829 standard |
| 6 | **Test Case Optimization** | Test case deduplicate ve önceliklendirme | Optimized JSON | 7+ Models | ✅ Risk-based testing |
| 7 | **Test Code Generation** | Otomatik test kodu (Selenium, API, Unit) | Code files | DeepSeek/Kimi | ✅ Framework agnostic |
| 8 | **Environment Setup** | Kurulum rehberi ve konfigürasyon | JSON Guide | LM Studio | ✅ DevOps best practices |
| 9 | **Test Execution** | Test running ve result collection | Execution Report | Custom Engine | ✅ CI/CD integration |
| 10 | **Test Reporting** | Comprehensive test raporları | HTML/PDF | Analytics Engine | ✅ Stakeholder ready |
| 11 | **Test Closure** | Final analiz ve lessons learned | Summary Report | Multi-source | ✅ Process improvement |

### 🎯 Akıllı Özellikler
- **Token limit yönetimi** - Büyük dosyalar için otomatik bölme ve chunking
- **Multi-model desteği** - LM Studio, OpenAI, Gemini, Ollama entegrasyonu
- **Session yönetimi** - Tüm işlemler MongoDB'de tracklenir
- **Dosya upload** - PDF, DOCX, TXT çoklu dosya desteği
- **Pipeline execution** - STLC adımlarını zincirleyebilme
- **Error handling** - Gemini API timeout ve finish_reason optimizasyonları
- **Performance monitoring** - Response time ve success rate takibi
- **Structured output** - JSON formatında standardize edilmiş çıktılar

## 🔧 Teknoloji Stack

### Backend
- **FastAPI** - Modern, hızlı web framework
- **Python 3.8+** - Core development language
- **MongoDB** - NoSQL database for session management
- **Pydantic** - Data validation and settings management
- **aiofiles** - Asynchronous file operations
- **PyPDF2** - PDF text extraction
- **python-docx** - Word document processing

### Frontend
- **React 18** - Modern UI library
- **Vite** - Fast build tool and dev server
- **JavaScript/JSX** - Frontend development
- **CSS3** - Modern styling with animations
- **Fetch API** - HTTP client for backend communication

### AI/ML Integration
- **Multiple LLM Support**:
  - OpenAI GPT models
  - Google Gemini Pro
  - LM Studio local models
  - Ollama local deployment
- **7+ Optimized Models** for different use cases
- **Intelligent fallback** mechanisms

## 📁 Proje Dizini

```
STLC-Manager/
├── frontend/                     # React Frontend Uygulaması
│   ├── src/
│   │   ├── components/          # UI Bileşenleri
│   │   │   ├── FileUpload.jsx
│   │   │   ├── Header.jsx
│   │   │   ├── Pipeline.jsx
│   │   │   ├── ProcessPanel.jsx
│   │   │   └── ...
│   │   ├── services/           # API Servis Katmanı
│   │   │   └── openai.js
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   └── ...
│   ├── public/
│   │   └── index.html
│   ├── package.json
│   └── ...
├── backend/                     # FastAPI Backend Uygulaması
│   ├── app.py                  # Ana uygulama dosyası
│   ├── config.py               # Konfigürasyon ayarları
│   ├── requirements.txt        # Python bağımlılıkları
│   ├── core/                   # Temel sistem bileşenleri
│   │   ├── __init__.py
│   │   ├── database.py         # MongoDB bağlantı yönetimi
│   │   ├── file_handler.py     # Dosya işleme (PDF, DOCX, TXT)
│   │   ├── model_client.py     # LLM model entegrasyonu
│   │   └── prompt_manager.py   # Prompt yönetimi
│   ├── pipeline/               # Pipeline işlem yönetimi
│   │   ├── __init__.py
│   │   ├── pipeline_controller.py
│   │   └── pipeline_executor.py
│   ├── stlc/                   # STLC modül implementasyonları
│   │   ├── __init__.py
│   │   ├── code_review.py
│   │   ├── requirement_analysis.py
│   │   ├── test_planning.py
│   │   ├── test_scenario_generation.py
│   │   ├── test_scenario_optimization.py
│   │   ├── test_case_generation.py
│   │   ├── test_case_optimization.py
│   │   ├── test_code_generation.py
│   │   ├── environment_setup.py
│   │   ├── test_execution.py
│   │   ├── test_reporting.py
│   │   └── test_closure.py
│   └── utils/                  # Yardımcı araçlar
│       ├── __init__.py
│       ├── text_splitter.py    # Metin parçalama
│       └── validation.py       # Veri doğrulama
├── tests/                      # 🧪 Test Dosyaları (Organize Edilmiş)
│   ├── README.md              # Test dokümantasyonu
│   ├── unit/                  # Unit testleri
│   │   ├── test_api_*.py     # API testleri
│   │   ├── test_gemini_*.py  # Gemini model testleri
│   │   ├── test_bulk_*.py    # Bulk işlem testleri
│   │   └── ...
│   ├── integration/           # Entegrasyon testleri
│   │   ├── test_backend_llm_integration.py
│   │   ├── test_frontend_backend_integration.py
│   │   ├── test_end_to_end_demo.py
│   │   └── test_final_integration.py
│   ├── performance/           # Performans testleri
│   │   ├── test_*_speed.py   # Hız testleri
│   │   └── ...
│   ├── utils/                 # Test yardımcı araçları
│   │   ├── check_*.py        # Kontrol scriptleri
│   │   ├── debug_*.py        # Debug araçları
│   │   ├── setup_*.py        # Kurulum scriptleri
│   │   └── ...
│   └── results/               # Test sonuçları
│       ├── *.json           # JSON test sonuçları
│       └── *.html           # HTML test raporları
├── uploads/                    # Yüklenen dosyalar
├── README.md                  # Ana proje dokümantasyonu
├── .gitignore
└── ...
```

### Frontend (React)
- **src/components/**: Bileşenler (ör. `FileUpload`, `Pipeline`, `OutputPanel`)  
- **src/services/**: API çağrılarını yöneten servis fonksiyonları (`openai.js` vs.)  
- **.env** (isteğe bağlı): Backend API URL gibi konfigürasyonları barındırır.  
- **main.jsx / App.jsx**: Uygulamanın ana giriş noktası ve yönlendirme.

### Backend (FastAPI)
- **app.py**: FastAPI uygulamasının ana dosyası.  
- **config.py**: Ortak yapılandırma ve environment değişkenleri (Mongo URI, model URL vb.).  
- **requirements.txt**: Backend bağımlılıkları.

#### **core/**
- **database.py**: MongoDB bağlantısı ve temel veritabanı işlemleri.  
- **file_handler.py**: Dosya yükleme, PDF/DOCX/TXT metin çıkarma fonksiyonları.  
- **model_client.py**: LLM (Large Language Model) çağrısını yönetir.  
- **prompt_manager.py**: MongoDB’den system prompt, query_str gibi verileri çekmek.

#### **pipeline/**
- **pipeline_controller.py**: UI’den gelen STLC adım seçimlerini işleyerek hangi adımların sırayla çalıştırılacağını belirler.  
- **pipeline_executor.py**: Seçilen adımları sırasıyla çalıştırır ve sonuçlarını birleştirir.

#### **stlc/**
- Her adım için (`code_review`, `requirement_analysis`, `test_planning` vb.) ayrı bir dosya.  
- `run_step(input_data)` fonksiyonuyla her adım tek başına veya pipeline içinde çağrılabilir.

#### **utils/**
- **text_splitter.py**: Metin parçalama (chunking) işlemleri.  
- **validation.py**: LLM çıktılarının (structured_output) istenen formata uygunluğunu doğrulama.

## Akış Diyagramı (Mermaid)

Aşağıda, bir pipeline çalıştırma senaryosunun genel akışını gösteren basit bir **Mermaid** diyagramı bulunuyor:

```mermaid
flowchart LR
    A[UI / Frontend] --> B[Pipeline Controller]
    B --> C[Pipeline Executor]
    C --> D[STLC Adım 1 (Ör: Test Planning)]
    C --> E[STLC Adım 2 (Ör: Test Case Generation)]
    C --> F[STLC Adım 3 (Ör: Test Reporting)]
    D --> C
    E --> C
    F --> G[Nihai Sonuç Dönüşü]
```

1. **UI / Frontend**: Kullanıcı, hangi STLC adımlarının seçileceğini belirler (checkbox vb.).  
2. **Pipeline Controller**: Seçilen adımları analiz eder, sırayı belirler.  
3. **Pipeline Executor**: Sırayla her STLC modülünün `run_step` fonksiyonunu çağırır.  
4. **STLC Adımları**: Her adım, ilgili verileri işleyerek kendi çıktısını üretir. Gerekirse bir sonraki adıma veri aktarılır.  
5. **Nihai Sonuç**: Tüm adımlar tamamlandığında, sonuç birleşik olarak UI’a döndürülür.

## 🚀 Nasıl Çalıştırılır?

### 1. Backend Kurulumu
```bash
cd STLC-Manager/backend
pip install -r requirements.txt
python app.py
```
- Uygulama varsayılan olarak `http://0.0.0.0:8000` üzerinde çalışacaktır.

### 2. Frontend Kurulumu
```bash
cd STLC-Manager/frontend
npm install
npm run dev
```
- Varsayılan olarak `http://localhost:5173` vb. bir portta çalışır (Vite/CRA ayarlarına göre değişebilir).

### 3. Testleri Çalıştırma
```bash
# Tüm testleri çalıştır
python -m pytest tests/

# Kategori bazlı test çalıştırma
python -m pytest tests/unit/           # Unit testleri
python -m pytest tests/integration/   # Entegrasyon testleri
python -m pytest tests/performance/   # Performans testleri

# Belirli bir test dosyası çalıştır
python tests/unit/test_gemini_fix.py
```

### 4. Env Değişkenleri (Örnek .env Dosyası)

```bash
# Backend
MONGO_URI=mongodb://localhost:27017
MODEL_API_BASE_URL=http://localhost:1234
MODEL_IDENTIFIER=llama-3.2-3b-instruct

# Frontend
REACT_APP_API_BASE_URL=http://localhost:8000
```

İhtiyaçlarınıza göre özelleştirin.

### 5. Kullanım Senaryoları
   - **Tek Adım**: Örneğin, `Test Planning` adımını tek başına çalıştırmak için UI’daki ilgili sayfadan dosya yükleyip “Çalıştır” butonuna basabilirsiniz.  
   - **Pipeline**: Checkbox’larla birden fazla adım (örn. `Test Planning`, `Test Case Generation`, `Test Reporting`) seçilip “Pipeline Çalıştır” denildiğinde, adımlar sırasıyla çalıştırılır ve toplu sonuç ekranda gösterilir.

## Katkıda Bulunma

- Yeni STLC adımları eklemek için `stlc` klasörüne `.py` dosyası ekleyip `run_step` fonksiyonunu tanımlayın.  
- Yeni bir model veya farklı bir vektör veritabanı eklemek için `core/model_client.py` veya `core/database.py` dosyalarında değişiklik yapın.  
- Pull Request’ler, bug raporları ve geliştirme önerileri memnuniyetle karşılanır!

## 📞 Destek & İletişim

### 🐛 Bug Raporları
Herhangi bir hata ile karşılaşırsanız lütfen GitHub Issues bölümünden bildirin.

### 💡 Feature Requests
Yeni özellik önerileri için GitHub Discussions kullanabilirsiniz.

### 📋 Roadmap
- [ ] Real-time collaboration features
- [ ] Advanced analytics dashboard  
- [ ] CI/CD pipeline integrations
- [ ] Multi-language support
- [ ] Enterprise authentication
- [ ] Custom model training

## 📜 Lisans

Bu proje MIT Lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakabilirsiniz.

## 🌟 Teşekkürler

Bu proje aşağıdaki açık kaynak projelerden ilham almıştır:
- FastAPI framework
- React ecosystem
- MongoDB community
- OpenAI & Google AI research
- ISTQB testing standards

---

**STLC Manager** - Yazılım Test Yaşam Döngüsünü AI ile güçlendiren modern çözüm 🚀
