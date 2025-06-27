"""
model_client.py
---------------
LLM (Large Language Model) çağrılarını yöneten katman.
Örneğin, ChatOpenAI gibi modelleri buradan çağırabilirsiniz.
"""

import logging
from langchain_openai import ChatOpenAI
from config import MODEL_API_BASE_URL, MODEL_IDENTIFIER

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
    selected_model = model_name if model_name else MODEL_IDENTIFIER
    
    # 1. Yapılandırma kontrolü
    if not MODEL_API_BASE_URL:
        logger.error("MODEL_API_BASE_URL boş olamaz.")
        raise ValueError("MODEL_API_BASE_URL yapılandırması eksik.")
    if not selected_model:
        logger.error("Model identifier boş olamaz.")
        raise ValueError("Model identifier yapılandırması eksik.")
    
    # 2. Model nesnesi oluşturma ve hata yakalama
    try:
        logger.info(f"LLM nesnesi oluşturuluyor: {selected_model} @ {MODEL_API_BASE_URL}")
        # LM Studio uses /v1/ prefix for OpenAI compatibility
        api_base_url = MODEL_API_BASE_URL if MODEL_API_BASE_URL.endswith('/v1') else f"{MODEL_API_BASE_URL}/v1"
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

class LLMClient:
    def __init__(self, model_name=None):
        self.api_url = "http://localhost:1234/v1"
        # Default model kullan veya parametre olarak verilen modeli al
        self.model_name = model_name if model_name else "llama-3.2-1b-instruct"
        self.logger = logging.getLogger("LLMClient")
        self.logger.info(f"LLMClient initialized with model: {self.model_name}")
        
    def get_model_identifier(self, model_key):
        """Frontend'den gelen model anahtarına göre gerçek model identifier'ını döndürür"""
        self.logger.info(f"Getting model identifier for key: {model_key}")
        if not model_key or not isinstance(model_key, str):
            self.logger.warning(f"Invalid model_key: {model_key}, using default model")
            return "llama-3.2-1b-instruct"  # Default model
            
        model_mapping = {
        "codegeex4:9b": "codegeex4-all-9b",
        "codellama:7b": "codellama-7b-instruct",
        "deepseek-coder:6.7b": "deepseek-coder-6.7b-instruct",
        "gemma2:2b": "gemma-2-2b-it",
        "gemma3:4b": "gemma-3-4b-it",
        "llama3.2:3b": "llama-3.2-3b-instruct",
        "llama-3.2-3b-instruct": "llama-3.2-3b-instruct",  # Fallback case
        "qwen2.5:7b": "qwen2.5-7b-instruct-1m",
        "qwen2.5:7b-1m": "qwen2.5-7b-instruct-1m",  # Büyük içerikler için özel mapping
        "qwen2.5-coder:3b": "qwen2.5-coder-3b-instruct",
        "stable-code:3b": "stable-code-instruct-3b",
        "starcoder2:7b": "starcoder2-7b"
        }

        
        model_id = model_mapping.get(model_key, None)
        self.logger.info(f"Model id: {model_id}")
        self.logger.info(f"Model mapping: {model_mapping}")
        if not model_id:
            self.logger.warning(f"Unknown model_key: {model_key}, using default model")
            return "llama-3.2-1b-instruct"  # Default model
            
        self.logger.info(f"Selected model: {model_key} -> {model_id}")
        return model_id

    async def generate_response(self, prompt, temperature=0.7, max_tokens=4096, response_format=None):
        """LLM API çağrısı yapan temel metod"""
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
