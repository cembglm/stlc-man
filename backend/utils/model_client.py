"""
model_client.py
---------------
LLM (Large Language Model) çağrılarını yöneten katman.
Örneğin, ChatOpenAI gibi modelleri buradan çağırabilirsiniz.
"""

import logging
from langchain_openai import ChatOpenAI
import sys
import os
# Add the backend directory to the path to import config
backend_dir = os.path.dirname(os.path.dirname(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)
# Import from the config.py file directly
import config
from google import genai
import json
import time
import asyncio
from typing import Dict, Optional

# Logger ayarları (hataları ve bilgileri takip etmek için)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def get_llm_instance(model_name: str = None, temperature: float = 0.7):
    """
    LLM nesnesini oluşturur ve bağlantıyı test eder.
    
    :param model_name: Kullanılacak model adı (opsiyonel).
    :param temperature: Modelin yaratıcılık seviyesi (varsayılan: 0.7).
    :return: ChatOpenAI nesnesi.
    :raises ValueError: Yapılandırma hataları için.
    :raises ConnectionError: Bağlantı hataları için.
    """
    # Model seçimi - eğer model_name verilmemişse default kullan
    selected_model = model_name if model_name else config.MODEL_IDENTIFIER
    
    # 1. Yapılandırma kontrolü
    if not config.MODEL_API_BASE_URL:
        logger.error("MODEL_API_BASE_URL boş olamaz.")
        raise ValueError("MODEL_API_BASE_URL yapılandırması eksik.")
    if not selected_model:
        logger.error("Model identifier boş olamaz.")
        raise ValueError("Model identifier yapılandırması eksik.")
    
    # 2. Model nesnesi oluşturma ve hata yakalama
    try:
        logger.info(f"LLM nesnesi oluşturuluyor: {selected_model} @ {config.MODEL_API_BASE_URL}")
        # LM Studio uses /v1/ prefix for OpenAI compatibility
        api_base_url = config.MODEL_API_BASE_URL if config.MODEL_API_BASE_URL.endswith('/v1') else f"{config.MODEL_API_BASE_URL}/v1"
        logger.info(f"Using API base URL: {api_base_url}")
        
        llm = ChatOpenAI(
            model_name=selected_model,
            openai_api_base=api_base_url,
            openai_api_key="not-needed",  # Gerekirse environment'tan çekilebilir
            temperature=temperature
        )
        
        # 3. Bağlantıyı test etme
        logger.debug(f"LLM'e gönderilen test sorgusu: Merhaba, bu bir test sorgusudur.")
        test_response = llm.invoke("Merhaba, bu bir test sorgusudur.")
        logger.debug(f"LLM'den alınan yanıt: {test_response}")
        if test_response:
            logger.info("LLM bağlantısı başarılı.")
        else:
            logger.warning("LLM'den yanıt alınamadı.")
        
        return llm
    except Exception as e:
        logger.error(f"LLM nesnesi oluşturulurken hata: {str(e)}")
        raise ConnectionError(f"LLM sunucusuna bağlanılamadı: {str(e)}")

import requests
import logging
import random

class LLMClient:
    # Sınıf seviyesinde rate limiting bilgileri (tüm instance'lar arasında paylaşılır)
    _rate_limits: Dict[str, Dict] = {}  # model_name -> {last_request_time, requests_per_minute, is_rate_limited}
    # Global istek sayacı - tüm modeller için
    _global_request_counter: int = 0
    
    # API tabanlı modeller için varsayılan sınırlar
    DEFAULT_RATE_LIMITS = {
        'gemini': {
            'requests_per_minute': 10,  # Gemini Tier 1 sınırı
            'cooldown_seconds': 5,     # 5 saniye base cooldown
            'random_delay_min': 2,      # Minimum rastgele bekleme (saniye)
            'random_delay_max': 30      # Maksimum rastgele bekleme (saniye)
        }
    }
    
    def __init__(self, model_name=None, api_key=None):
        self.api_url = "http://localhost:1234/v1"
        # Default model kullan veya parametre olarak verilen modeli al
        self.model_name = model_name if model_name else "llama-3.2-1b-instruct"
        self.api_key = api_key  # Gemini API key'i için
        self.logger = logging.getLogger("LLMClient")
        self.logger.info(f"LLMClient initialized with model: {self.model_name}")
        
        # Gemini model kontrolü
        self.is_gemini = self._is_gemini_model(self.model_name)
        self.is_api_based = self.is_gemini  # Şu an sadece Gemini API tabanlı, gelecekte genişletilebilir
        
        if self.is_gemini:
            self.logger.info(f"Gemini model detected: {self.model_name}")
            if not self.api_key:
                raise ValueError("API key is required for Gemini models")
            # Gemini client'ı başlat
            try:
                # Gemini client oluştur
                self.gemini_client = genai.Client(api_key=self.api_key)
                self.logger.info("Gemini client initialized successfully")
                
                # Rate limiting bilgilerini başlat
                self._init_rate_limiting()
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini client: {e}")
                raise
        
    def _is_gemini_model(self, model_name):
        """Model isminin Gemini modeli olup olmadığını kontrol et"""
        if not model_name:
            return False
        gemini_models = [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-pro",
            "gemini-flash"
        ]
        return any(gemini_model in model_name.lower() for gemini_model in gemini_models)
    
    def _init_rate_limiting(self):
        """API tabanlı modeller için rate limiting bilgilerini başlat"""
        if not self.is_api_based:
            return
            
        model_key = self._get_rate_limit_key()
        if model_key not in self._rate_limits:
            self._rate_limits[model_key] = {
                'request_times': [],  # Son isteklerin zamanları
                'is_rate_limited': False,
                'last_error_time': None,
                'consecutive_errors': 0
            }
            
    def _get_rate_limit_key(self) -> str:
        """Rate limiting için kullanılacak anahtarı döndür"""
        if self.is_gemini:
            return f"gemini_{self.model_name}"
        return f"api_{self.model_name}"
    
    def _get_rate_limit_config(self) -> Dict:
        """Model için rate limiting konfigürasyonunu döndür"""
        if self.is_gemini:
            return self.DEFAULT_RATE_LIMITS['gemini']
        # Gelecekte diğer API'lar için genişletilebilir
        return {
            'requests_per_minute': 60, 
            'cooldown_seconds': 30,
            'random_delay_min': 2,
            'random_delay_max': 30
        }  # Default
    
    async def _check_and_apply_rate_limit(self):
        """Rate limiting kontrolü yap ve gerekirse bekle"""
        if not self.is_api_based:
            return  # Local modeller için rate limiting yok
            
        # İstek numarasını artır
        LLMClient._global_request_counter += 1
        current_request_number = LLMClient._global_request_counter
        
        model_key = self._get_rate_limit_key()
        rate_config = self._get_rate_limit_config()
        current_time = time.time()
        
        # Rate limit bilgilerini al
        rate_info = self._rate_limits.get(model_key, {})
        request_times = rate_info.get('request_times', [])
        
        # 1 dakikadan eski istekleri temizle
        request_times = [t for t in request_times if current_time - t < 60]
        
        # Base cooldown + rastgele bekleme hesapla
        base_cooldown = rate_config['cooldown_seconds']
        random_delay = random.uniform(rate_config['random_delay_min'], rate_config['random_delay_max'])
        total_wait_time = base_cooldown + random_delay
        
        self.logger.info(f"🔄 API Request #{current_request_number} - Model: {self.model_name}")
        self.logger.info(f"⏱️  Applying cooldown: {base_cooldown}s + random delay: {random_delay:.2f}s = Total: {total_wait_time:.2f}s")
        
        # Her istekten önce total_wait_time kadar bekle (spam önleme)
        await asyncio.sleep(total_wait_time)
        
        # Eğer rate limit aktifse ve henüz cooldown süresi geçmediyse
        if rate_info.get('is_rate_limited', False):
            last_error_time = rate_info.get('last_error_time', 0)
            cooldown_seconds = rate_config['cooldown_seconds']
            
            if current_time - last_error_time < cooldown_seconds:
                remaining_time = cooldown_seconds - (current_time - last_error_time)
                additional_random = random.uniform(rate_config['random_delay_min'], rate_config['random_delay_max'])
                total_additional_wait = remaining_time + additional_random
                
                self.logger.warning(f"🚫 Rate limit active for {model_key}. Additional wait: {remaining_time:.1f}s + {additional_random:.2f}s = {total_additional_wait:.2f}s")
                await asyncio.sleep(total_additional_wait)
                # Rate limit'i sıfırla
                rate_info['is_rate_limited'] = False
                rate_info['consecutive_errors'] = 0
        
        # İstek sayısı kontrolü
        requests_per_minute = rate_config['requests_per_minute']
        if len(request_times) >= requests_per_minute:
            # Rate limit aşılacak, bekle
            oldest_request = min(request_times)
            wait_time = 60 - (current_time - oldest_request) + 1  # 1 saniye ekstra güvenlik
            additional_random = random.uniform(rate_config['random_delay_min'], rate_config['random_delay_max'])
            total_prevention_wait = wait_time + additional_random
            
            if wait_time > 0:
                self.logger.info(f"🛡️  Rate limit prevention: {wait_time:.1f}s + {additional_random:.2f}s = {total_prevention_wait:.2f}s for {model_key}")
                await asyncio.sleep(total_prevention_wait)
                current_time = time.time()
                # Eski istekleri tekrar temizle
                request_times = [t for t in request_times if current_time - t < 60]
        
        # Bu isteği kaydet
        request_times.append(current_time)
        rate_info['request_times'] = request_times
        self._rate_limits[model_key] = rate_info
    
    def _handle_rate_limit_error(self, error_response: str):
        """Rate limit hatası geldiğinde çağrılan metod"""
        if not self.is_api_based:
            return
            
        model_key = self._get_rate_limit_key()
        rate_info = self._rate_limits.get(model_key, {})
        rate_config = self._get_rate_limit_config()
        
        # Rate limit aktif olarak işaretle
        rate_info['is_rate_limited'] = True
        rate_info['last_error_time'] = time.time()
        rate_info['consecutive_errors'] = rate_info.get('consecutive_errors', 0) + 1
        
        # Rastgele bekleme süresini hesapla
        random_delay = random.uniform(rate_config['random_delay_min'], rate_config['random_delay_max'])
        base_cooldown = rate_config['cooldown_seconds']
        
        # Eğer sürekli rate limit hatası alıyorsak, daha uzun bekle
        if rate_info['consecutive_errors'] > 3:
            base_cooldown = min(base_cooldown * 2, 120)  # Max 2 dakika base cooldown
            self.logger.warning(f"⚠️  Increasing base cooldown to {base_cooldown}s due to repeated rate limits")
        
        total_wait = base_cooldown + random_delay
        self.logger.error(f"🚫 Rate limit detected for {model_key}. Next wait will be: {base_cooldown}s + {random_delay:.2f}s = {total_wait:.2f}s")
        
        self._rate_limits[model_key] = rate_info
        
        
    def get_model_identifier(self, model_key):
        """Frontend'den gelen model anahtarına göre gerçek model identifier'ını döndürür"""
        self.logger.info(f"Getting model identifier for key: {model_key}")
        if not model_key or not isinstance(model_key, str):
            self.logger.warning(f"Invalid model_key: {model_key}, using default model")
            return "llama-3.2-1b-instruct"  # Default model
        
        # Merkezi konfigürasyondan model mapping'i al
        try:
            from config.models_config import get_model_by_key
            model_config = get_model_by_key(model_key)
            
            if model_config:
                # Modelin identifier'ını al (LM Studio için)
                model_id = self._get_lm_studio_identifier(model_key, model_config)
                self.logger.info(f"Selected model from config: {model_key} -> {model_id}")
                return model_id
            else:
                self.logger.warning(f"Model key '{model_key}' not found in central config")
        except ImportError as e:
            self.logger.warning(f"Could not import central config: {e}, falling back to local mapping")
        except Exception as e:
            self.logger.warning(f"Error accessing central config: {e}, falling back to local mapping")
        
        # Fallback: Eski hardcoded mapping (geriye uyumluluk için)
        model_mapping = {
            "codegeex4:9b": "codegeex4-all-9b",
            "codellama:7b": "codellama-7b-instruct",
            "deepseek-coder:6.7b": "deepseek-coder-6.7b-instruct",
            "gemma2:2b": "gemma-2-2b-it",
            "gemma3:4b": "gemma-3-4b-it",
            "google/gemma-3-12b": "gemma-3-12b-it",
            "llama3.2:3b": "llama-3.2-3b-instruct",
            "llama-3.2-3b-instruct": "llama-3.2-3b-instruct",  # Fallback case
            "meta/llama-3.3-70b": "meta/llama-3.3-70b",
            "mistralai/codestral-22b-v0.1": "mistralai/codestral-22b-v0.1",
            "openai/gpt-oss-20b": "openai/gpt-oss-20b",
            "qwen/qwq-32b": "qwen/qwq-32b",
            "qwen2.5:7b": "qwen2.5-7b-instruct-1m",
            "qwen2.5:7b-1m": "qwen2.5-7b-instruct-1m",
            "qwen2.5-coder:3b": "qwen2.5-coder-3b-instruct",
            "qwen/qwen3-14b": "qwen3-14b-instruct",
            "stable-code:3b": "stable-code-instruct-3b",
            "starcoder2:7b": "starcoder2-7b",
            # Yeni Test Case Optimization modelleri
            "codellama:70b-instruct": "CodeLlama-70B-Instruct-GGUF/codellama-70b-instruct.Q4_K_S.gguf",
            "kimi-dev:72b": "Kimi-Dev-72B-GGUF/Kimi-Dev-72B-Q3_K_S.gguf",
            "openai/gpt-oss-120b": "openai/gpt-oss-120b",
            "deepseek-r1-distill:32b": "DeepSeek-R1-Distill-Qwen-32B-GGUF/DeepSeek-R1-Distill-Qwen-32B-Q3_K_L.gguf",
            "google/gemma-3-27b": "google/gemma-3-27b",
            "qwen/qwen3-coder-30b": "qwen/qwen3-coder-30b",
            "deepseek/deepseek-r1-qwen3-8b": "deepseek/deepseek-r1-0528-qwen3-8b"
        }
        
        model_id = model_mapping.get(model_key, None)
        self.logger.info(f"Model id from fallback mapping: {model_id}")
        if not model_id:
            self.logger.warning(f"Unknown model_key: {model_key}, using default model")
            return "llama-3.2-1b-instruct"  # Default model
            
        self.logger.info(f"Selected model (fallback): {model_key} -> {model_id}")
        return model_id

    def _get_lm_studio_identifier(self, model_key, model_config):
        """Model konfigürasyonuna göre LM Studio identifier'ını döndür"""
        # API modelleri için direkt model key'i kullan
        if model_config.get("type") == "api":
            return model_key
        
        # Local modeller için özel mapping'ler
        special_mappings = {
            "codegeex4:9b": "codegeex4-all-9b",
            "codellama:7b": "codellama-7b-instruct",
            "deepseek-coder:6.7b": "deepseek-coder-6.7b-instruct",
            "gemma2:2b": "gemma-2-2b-it",
            "gemma3:4b": "gemma-3-4b-it",
            "google/gemma-3-12b": "gemma-3-12b-it",
            "llama3.2:3b": "llama-3.2-3b-instruct",
            "qwen2.5:7b": "qwen2.5-7b-instruct-1m",
            "qwen2.5:7b-1m": "qwen2.5-7b-instruct-1m",
            "qwen2.5-coder:3b": "qwen2.5-coder-3b-instruct",
            "qwen/qwen3-14b": "qwen3-14b-instruct",
            "stable-code:3b": "stable-code-instruct-3b",
            "starcoder2:7b": "starcoder2-7b",
            # Büyük modeller için özel GGUF path'leri
            "codellama:70b-instruct": "CodeLlama-70B-Instruct-GGUF/codellama-70b-instruct.Q4_K_S.gguf",
            "kimi-dev:72b": "Kimi-Dev-72B-GGUF/Kimi-Dev-72B-Q3_K_S.gguf",
            "deepseek-r1-distill:32b": "DeepSeek-R1-Distill-Qwen-32B-GGUF/DeepSeek-R1-Distill-Qwen-32B-Q3_K_L.gguf",
            "deepseek/deepseek-r1-qwen3-8b": "deepseek/deepseek-r1-0528-qwen3-8b"
        }
        
        # Önce özel mapping'lere bak
        if model_key in special_mappings:
            return special_mappings[model_key]
        
        # Yoksa direkt model key'i kullan
        return model_key

    async def generate_response(self, prompt, temperature=0.7, max_tokens=4096, response_format=None):
        """LLM API çağrısı yapan temel metod - rate limiting ile"""
        
        # API tabanlı modeller için rate limiting kontrolü
        if self.is_api_based:
            await self._check_and_apply_rate_limit()
        
        # Gemini modeli kontrolü
        if self.is_gemini:
            return await self._generate_gemini_response(prompt, temperature, max_tokens)
        
        # LM Studio için mevcut kod (rate limiting yok)
        # self.model_name yerine get_model_identifier sonucunu kullan
        actual_model = self.model_name
        if hasattr(self, 'original_key'):
            actual_model = self.get_model_identifier(self.original_key)
            
        payload = {
            "model": actual_model,
            "messages": [{"role": "system", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        # Note: LM Studio doesn't support response_format parameter, so we ignore it
        # The calling code should handle JSON parsing from the text response
        if response_format:
            self.logger.info(f"Ignoring response_format parameter as LM Studio doesn't support it: {response_format}")
            
        try:
            self.logger.debug(f"Sending request to LLM API with model: {actual_model}")
            self.logger.debug(f"Request payload: {payload}")
            self.logger.info(f"Making POST request to: {self.api_url}/chat/completions")
            
            # Add timeout configuration to prevent hanging
            response = requests.post(
                f"{self.api_url}/chat/completions", 
                json=payload, 
                timeout=300  # 300 second timeout (5 minutes) for complex test case generation
            )
            response.raise_for_status()
            
            self.logger.debug(f"Response status code: {response.status_code}")
            response_json = response.json()
            self.logger.debug(f"Response JSON keys: {list(response_json.keys())}")
            
            if "choices" not in response_json or not response_json["choices"]:
                self.logger.error(f"Invalid response format: {response_json}")
                raise ValueError("Invalid response format from LLM API")
            
            result = response_json["choices"][0]["message"]["content"]
            self.logger.info(f"Successfully generated response with model: {actual_model}")
            return result
        except requests.Timeout as e:
            self.logger.error(f"Timeout error when calling LLM API with model {actual_model}: {str(e)}")
            raise TimeoutError(f"LLM API request timed out after 300 seconds (5 minutes)")
        except requests.RequestException as e:
            self.logger.error(f"LLM API Error with model {actual_model}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Response status: {e.response.status_code}")
                self.logger.error(f"Response text: {e.response.text}")
            raise

    async def _generate_gemini_response(self, prompt, temperature=0.7, max_tokens=4096):
        """Gemini API çağrısı yapan metod - 503 hataları için özel retry mekanizması ile"""
        try:
            self.logger.debug(f"Sending request to Gemini API with model: {self.model_name}")
            self.logger.debug(f"Prompt: {prompt[:100]}...")  # İlk 100 karakteri log'la
            
            # Gemini API çağrısı
            response = self.gemini_client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                # Gemini için temperature ve max_tokens parametreleri farklı şekilde ayarlanabilir
                # Bu kısım Gemini API dokümantasyonuna göre ayarlanabilir
            )
            
            if response and hasattr(response, 'text'):
                result = response.text
                self.logger.info(f"✅ Successfully generated response with Gemini model: {self.model_name}")
                self.logger.info(f"📊 Gemini response length: {len(result)}")
                self.logger.info(f"📄 Gemini response preview: {result[:200]}...")
                return result
            else:
                self.logger.error(f"❌ Invalid response from Gemini API: {response}")
                raise ValueError("Invalid response format from Gemini API")
                
        except Exception as e:
            error_str = str(e)
            
            # 503 Service Unavailable hatası kontrolü
            if "503" in error_str or "service unavailable" in error_str.lower() or "unavailable" in error_str.lower():
                rate_config = self._get_rate_limit_config()
                base_cooldown = rate_config['cooldown_seconds']
                random_delay = random.uniform(rate_config['random_delay_min'], rate_config['random_delay_max'])
                total_wait = base_cooldown + random_delay
                
                self.logger.warning(f"🔴 503 Service Unavailable detected for Gemini API")
                self.logger.warning(f"⏳ Google servers are overloaded. Model is currently unavailable.")
                self.logger.warning(f"🔄 Will wait {base_cooldown}s + {random_delay:.2f}s = {total_wait:.2f}s before retry")
                
                # 503 hatası için rate limit işaretle (ancak hata fırlatma, retry'ı üst katmana bırak)
                self._handle_rate_limit_error(error_str)
                raise Exception(f"Gemini API is temporarily unavailable (503). Wait time applied: {total_wait:.2f}s. Error: {error_str}")
            
            # 500 Internal Error kontrolü
            elif "500" in error_str and "internal" in error_str.lower():
                rate_config = self._get_rate_limit_config()
                base_cooldown = 2  # 500 için biraz daha kısa bekleme
                random_delay = random.uniform(2, 20)
                total_wait = base_cooldown + random_delay
                
                self.logger.warning(f"🔴 500 Internal Error detected for Gemini API")
                self.logger.warning(f"⚙️  Google API internal error. Server issue.")
                self.logger.warning(f"🔄 Will wait {base_cooldown}s + {random_delay:.2f}s = {total_wait:.2f}s before retry")
                
                # 500 hatası için de rate limit işaretle
                self._handle_rate_limit_error(error_str)
                raise Exception(f"Gemini API internal error (500). Wait time applied: {total_wait:.2f}s. Error: {error_str}")
            
            # Diğer rate limit hataları kontrolü
            elif "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                self.logger.warning(f"🔴 Rate limit detected in Gemini API: {error_str}")
                self._handle_rate_limit_error(error_str)
                
                # Rate limit hatası durumunda tekrar deneme yapma, 
                # bunun yerine hata fırlat ve üst katmanın handle etmesini bekle
                raise Exception(f"Rate limit exceeded for Gemini API. Please wait and try again. Error: {error_str}")
            
            self.logger.error(f"❌ Gemini API Error with model {self.model_name}: {error_str}")
            raise
