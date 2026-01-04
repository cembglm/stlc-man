import { useState, useCallback } from 'react';

/**
 * Pipeline Configuration Hook
 * 
 * Her process için yapılan ayarlamaları yönetir.
 * Backend API'larla tam uyumlu config formatı sağlar.
 */
export function usePipelineConfig() {
  // Her process için yapılandırma durumu
  const [pipelineConfigs, setPipelineConfigs] = useState({});
  
  /**
   * Bir process için konfigürasyonu kaydet
   * @param {string} processId - Process ID (örn: 'test-scenario-generation')
   * @param {object} config - Process configuration
   */
  const saveProcessConfig = useCallback((processId, config) => {
    setPipelineConfigs(prev => ({
      ...prev,
      [processId]: {
        ...config,
        isConfigured: true,
        configuredAt: new Date().toISOString()
      }
    }));
    console.log(`[usePipelineConfig] Configuration saved for ${processId}:`, config);
  }, []);
  
  /**
   * Bir process'in konfigürasyonunu al
   * @param {string} processId - Process ID
   * @returns {object|null} Process configuration veya null
   */
  const getProcessConfig = useCallback((processId) => {
    return pipelineConfigs[processId] || null;
  }, [pipelineConfigs]);
  
  /**
   * Bir process'in configure edilip edilmediğini kontrol et
   * @param {string} processId - Process ID
   * @returns {boolean} Configure edilmiş mi?
   */
  const isProcessConfigured = useCallback((processId) => {
    return pipelineConfigs[processId]?.isConfigured === true;
  }, [pipelineConfigs]);
  
  /**
   * Bir process'in konfigürasyonunu sil
   * @param {string} processId - Process ID
   */
  const clearProcessConfig = useCallback((processId) => {
    setPipelineConfigs(prev => {
      const newConfigs = { ...prev };
      delete newConfigs[processId];
      return newConfigs;
    });
    console.log(`[usePipelineConfig] Configuration cleared for ${processId}`);
  }, []);
  
  /**
   * Tüm konfigürasyonları temizle
   */
  const clearAllConfigs = useCallback(() => {
    setPipelineConfigs({});
    console.log('[usePipelineConfig] All configurations cleared');
  }, []);
  
  /**
   * Pipeline'da seçili olan tüm process'lerin configure durumunu kontrol et
   * @param {Set} selectedProcesses - Seçili process ID'leri
   * @returns {object} { allConfigured: boolean, missingConfigs: string[] }
   */
  const validatePipelineConfigs = useCallback((selectedProcesses) => {
    const processArray = Array.from(selectedProcesses);
    const missingConfigs = processArray.filter(processId => !isProcessConfigured(processId));
    
    return {
      allConfigured: missingConfigs.length === 0,
      missingConfigs,
      configuredCount: processArray.length - missingConfigs.length,
      totalCount: processArray.length
    };
  }, [isProcessConfigured]);
  
  /**
   * Process konfigürasyonunu backend API formatına dönüştür
   * @param {string} processId - Process ID
   * @returns {object|null} Backend'e gönderilecek config veya null
   */
  const getBackendConfig = useCallback((processId) => {
    const config = pipelineConfigs[processId];
    if (!config) return null;
    
    // Backend API'larla uyumlu format
    // Her process'in kendi API formatına göre dönüştürme yapılabilir
    const backendConfig = {
      ...config,
      processId,
      // Backend'e gönderilmeyecek frontend-only alanları kaldır
      isConfigured: undefined,
      configuredAt: undefined
    };
    
    // Undefined alanları temizle
    Object.keys(backendConfig).forEach(key => {
      if (backendConfig[key] === undefined) {
        delete backendConfig[key];
      }
    });
    
    return backendConfig;
  }, [pipelineConfigs]);
  
  return {
    pipelineConfigs,
    saveProcessConfig,
    getProcessConfig,
    isProcessConfigured,
    clearProcessConfig,
    clearAllConfigs,
    validatePipelineConfigs,
    getBackendConfig
  };
}
