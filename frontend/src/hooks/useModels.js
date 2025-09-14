/**
 * useModels.js
 * ------------
 * Merkezi AI model yönetimi için React hook'u.
 * Tüm form componentlerde kullanılabilir.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

// API base URL
const API_BASE_URL = 'http://localhost:8000/api/models';

/**
 * Merkezi model yönetimi hook'u
 * @param {Object} options - Hook konfigürasyon seçenekleri
 * @param {string} options.filterType - Model tipi filtresi (local/api)
 * @param {string} options.filterCategory - Model kategorisi filtresi
 * @param {string} options.filterPerformance - Performans filtresi
 * @param {boolean} options.optimizationReady - Optimization-ready modeller
 * @param {boolean} options.fastOnly - Sadece hızlı modeller
 * @param {boolean} options.autoFetch - Otomatik fetch (default: true)
 * @param {boolean} options.includeDescriptions - Model açıklamalarını dahil et
 * @returns {Object} Hook state ve fonksiyonları
 */
export const useModels = (options = {}) => {
  const {
    filterType = null,
    filterCategory = null,
    filterPerformance = null,
    optimizationReady = null,
    fastOnly = false,
    autoFetch = true,
    includeDescriptions = true
  } = options;

  // State
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastFetch, setLastFetch] = useState(null);

  // Cache için model açıklamaları
  const [modelDescriptions, setModelDescriptions] = useState({});

  /**
   * API'den modelleri getir
   */
  const fetchModels = useCallback(async (customFilters = {}) => {
    setLoading(true);
    setError(null);

    try {
      // Filter parametrelerini hazırla
      const filters = {
        model_type: filterType,
        category: filterCategory,
        performance: filterPerformance,
        optimization_ready: optimizationReady,
        legacy_format: true, // Mevcut frontend uyumluluğu için
        ...customFilters
      };

      // Fast only filtresi varsa performans filtresi ekle
      if (fastOnly && !filters.performance) {
        // İki ayrı request ile fast ve very-fast modelleri al
        const fastResponse = await axios.get(`${API_BASE_URL}/fast`);
        if (fastResponse.data.success) {
          const fastModels = fastResponse.data.data.map(model => ({
            key: model.key,
            name: model.name,
            description: model.description,
            type: model.type,
            provider: model.provider,
            performance: model.performance,
            category: model.category
          }));
          setModels(fastModels);
          setLastFetch(new Date());
          setLoading(false);
          return fastModels;
        }
      }

      // Normal API çağrısı
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          params.append(key, value);
        }
      });

      const response = await axios.get(`${API_BASE_URL}?${params}`);
      
      if (response.data.success) {
        const fetchedModels = response.data.data;
        setModels(fetchedModels);
        setLastFetch(new Date());

        // Model açıklamalarını getir (eğer istenmişse)
        if (includeDescriptions) {
          await fetchModelDescriptions(fetchedModels);
        }

        console.log(`[useModels] Fetched ${fetchedModels.length} models successfully`);
        return fetchedModels;
      } else {
        throw new Error(response.data.message || 'Failed to fetch models');
      }
    } catch (err) {
      console.error('[useModels] Error fetching models:', err);
      setError(err.message || 'Failed to fetch models');
      
      // Fallback: Static model listesi (geriye uyumluluk)
      const fallbackModels = getFallbackModels(filterType, filterCategory);
      setModels(fallbackModels);
      return fallbackModels;
    } finally {
      setLoading(false);
    }
  }, [filterType, filterCategory, filterPerformance, optimizationReady, fastOnly, includeDescriptions]);

  /**
   * Model açıklamalarını getir
   */
  const fetchModelDescriptions = useCallback(async (modelList) => {
    const descriptions = {};
    
    try {
      for (const model of modelList) {
        try {
          const response = await axios.get(`${API_BASE_URL}/${model.key}/descriptions`);
          if (response.data.success) {
            descriptions[model.key] = response.data.data.descriptions;
          }
        } catch (err) {
          // Sessizce geç, açıklama zorunlu değil
          console.warn(`[useModels] Could not fetch descriptions for ${model.key}`);
        }
      }
      
      setModelDescriptions(prev => ({ ...prev, ...descriptions }));
    } catch (err) {
      console.warn('[useModels] Error fetching model descriptions:', err);
    }
  }, []);

  /**
   * Belirli bir model hakkında detay getir
   */
  const getModelDetails = useCallback(async (modelKey) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/${modelKey}`);
      if (response.data.success) {
        return response.data.data;
      }
      throw new Error(response.data.message || 'Model not found');
    } catch (err) {
      console.error(`[useModels] Error fetching model details for ${modelKey}:`, err);
      return null;
    }
  }, []);

  /**
   * Modelleri yeniden getir
   */
  const refetch = useCallback((customFilters = {}) => {
    return fetchModels(customFilters);
  }, [fetchModels]);

  /**
   * Kategori listesini getir
   */
  const fetchCategories = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/categories`);
      if (response.data.success) {
        return response.data.data.categories;
      }
      throw new Error('Failed to fetch categories');
    } catch (err) {
      console.error('[useModels] Error fetching categories:', err);
      return ['code', 'general', 'reasoning', 'multilingual', 'development'];
    }
  }, []);

  /**
   * Performans seviyelerini getir
   */
  const fetchPerformanceLevels = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/performance-levels`);
      if (response.data.success) {
        return response.data.data.levels;
      }
      throw new Error('Failed to fetch performance levels');
    } catch (err) {
      console.error('[useModels] Error fetching performance levels:', err);
      return ['very-fast', 'fast', 'medium', 'slow', 'very-slow'];
    }
  }, []);

  // Otomatik fetch (component mount'ta)
  useEffect(() => {
    if (autoFetch) {
      fetchModels();
    }
  }, [autoFetch, fetchModels]);

  // Computed values
  const modelsByType = useMemo(() => {
    return models.reduce((acc, model) => {
      if (!acc[model.type]) acc[model.type] = [];
      acc[model.type].push(model);
      return acc;
    }, {});
  }, [models]);

  const modelsByCategory = useMemo(() => {
    return models.reduce((acc, model) => {
      const category = model.category || 'general';
      if (!acc[category]) acc[category] = [];
      acc[category].push(model);
      return acc;
    }, {});
  }, [models]);

  const fastModels = useMemo(() => {
    return models.filter(model => 
      ['fast', 'very-fast'].includes(model.performance)
    );
  }, [models]);

  const apiModels = useMemo(() => {
    return models.filter(model => model.type === 'api');
  }, [models]);

  const localModels = useMemo(() => {
    return models.filter(model => model.type === 'local');
  }, [models]);

  // Yardımcı fonksiyonlar
  const getModelByKey = useCallback((key) => {
    return models.find(model => model.key === key);
  }, [models]);

  const getModelDescriptions = useCallback((key) => {
    return modelDescriptions[key] || [];
  }, [modelDescriptions]);

  return {
    // Ana data
    models,
    loading,
    error,
    lastFetch,

    // Computed data
    modelsByType,
    modelsByCategory,
    fastModels,
    apiModels,
    localModels,

    // Model açıklamaları
    modelDescriptions,
    getModelDescriptions,

    // Fonksiyonlar
    fetchModels,
    refetch,
    getModelDetails,
    getModelByKey,
    fetchCategories,
    fetchPerformanceLevels,

    // Yardımcı fonksiyonlar
    hasModels: models.length > 0,
    isEmpty: models.length === 0,
    totalCount: models.length,
    localCount: localModels.length,
    apiCount: apiModels.length,
    fastCount: fastModels.length
  };
};

/**
 * Fallback model listesi (API erişilmediğinde)
 */
function getFallbackModels(filterType = null, filterCategory = null) {
  const fallbackModels = [
    // Temel modeller
    { key: "codegeex4:9b", name: "CodeGeeX4 (9B)", description: "Code generation optimized model", type: "local", category: "code" },
    { key: "codellama:7b", name: "Code Llama (7B)", description: "Meta's code-focused model", type: "local", category: "code" },
    { key: "deepseek-coder:6.7b", name: "DeepSeek Coder (6.7B)", description: "DeepSeek's coding model", type: "local", category: "code" },
    { key: "gemma2:2b", name: "Gemma 2 (2B)", description: "Google's lightweight model", type: "local", category: "general" },
    { key: "gemma3:4b", name: "Gemma 3 (4B)", description: "Google's enhanced model", type: "local", category: "general" },
    { key: "llama3.2:3b", name: "Llama 3.2 (3B)", description: "Meta's latest efficient model", type: "local", category: "general" },
    { key: "qwen2.5:7b", name: "Qwen 2.5 (7B)", description: "Alibaba's advanced model", type: "local", category: "multilingual" },
    { key: "qwen2.5-coder:3b", name: "Qwen 2.5 Coder (3B)", description: "Coding-focused Qwen model", type: "local", category: "code" },
    { key: "stable-code:3b", name: "Stable Code (3B)", description: "Stability AI's code model", type: "local", category: "code" },
    { key: "starcoder2:7b", name: "StarCoder 2 (7B)", description: "BigCode's enhanced model", type: "local", category: "code" },

    // API modelleri
    { key: "gemini-2.5-flash", name: "Gemini 2.5 Flash", description: "Google's latest fast model", type: "api", category: "general" },
    { key: "gemini-2.5-pro", name: "Gemini 2.5 Pro", description: "Google's latest pro model", type: "api", category: "general" }
  ];

  // Filtreleme uygula
  let filtered = fallbackModels;
  
  if (filterType) {
    filtered = filtered.filter(model => model.type === filterType);
  }
  
  if (filterCategory) {
    filtered = filtered.filter(model => model.category === filterCategory);
  }

  return filtered;
}

/**
 * Sadece hızlı modeller için özel hook
 */
export const useFastModels = () => {
  return useModels({ fastOnly: true });
};

/**
 * Test Case Optimization modelleri için özel hook
 */
export const useOptimizationModels = () => {
  return useModels({ optimizationReady: true });
};

/**
 * API modelleri için özel hook
 */
export const useApiModels = () => {
  return useModels({ filterType: 'api' });
};

/**
 * Local modeller için özel hook
 */
export const useLocalModels = () => {
  return useModels({ filterType: 'local' });
};

/**
 * Belirli bir kategori için modeller
 */
export const useModelsByCategory = (category) => {
  return useModels({ filterCategory: category });
};

export default useModels;