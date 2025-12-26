"""
test_code_generation.py
-----------------------
STLC'nin Test Code Generation adımına ait işlemleri yönetir.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from services.test_code_generation_service import TestCodeGenerationService
import logging
from typing import Optional, List

router = APIRouter()
logger = logging.getLogger("test_code_generation")
test_code_service = TestCodeGenerationService()

@router.get("/environment-setups")
async def get_environment_setups():
    """
    Mevcut environment setup kayıtlarını getirir
    """
    try:
        setups = test_code_service.get_environment_setups()
        return {
            "success": True,
            "data": setups,
            "count": len(setups)
        }
    except Exception as e:
        logger.error(f"Error getting environment setups: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/process-titles")
async def get_available_process_titles():
    """
    Mevcut process title'ları getirir (test case optimization'dan)
    """
    try:
        process_titles = test_code_service.get_available_process_titles()
        return {
            "success": True,
            "data": process_titles,
            "count": len(process_titles)
        }
    except Exception as e:
        logger.error(f"Error getting process titles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run")
async def process_test_code_generation(
    process_title: str = Form(...),
    environment_session_id: str = Form(...),
    files: List[UploadFile] = File(...),
    model: Optional[str] = Form("llama3.2:3b"),
    custom_prompt: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    environment_name: Optional[str] = Form(None),
    output_format: Optional[str] = Form("JSON"),
    api_key: Optional[str] = Form(None)
):
    """
    Standard process runner for test code generation
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No source files uploaded")
        
        if not process_title:
            raise HTTPException(status_code=400, detail="Process title is required")
            
        if not environment_session_id:
            raise HTTPException(status_code=400, detail="Environment session ID is required")
        
        if not environment_name or environment_name.strip() == "":
            raise HTTPException(status_code=400, detail="Test Code Generation Process Name is required")
        
        logger.info(f"Running test code generation process")
        logger.info(f"Process title: {process_title}")
        logger.info(f"Environment session: {environment_session_id}")
        logger.info(f"Session ID: {session_id}")
        logger.info(f"Environment name: {environment_name}")
        logger.info(f"Files count: {len(files)}")
        logger.info(f"Model: {model}")
        logger.info(f"Output format: {output_format}")
        logger.info(f"API key provided: {'Yes' if api_key else 'No'}")
        if api_key:
            logger.info(f"API key preview: {api_key[:15]}...")
        
        result = await test_code_service.generate_test_codes(
            process_title=process_title,
            environment_session_id=environment_session_id,
            source_files=files,
            model_name=model,
            custom_prompt=custom_prompt,
            session_id=session_id,
            environment_name=environment_name,
            output_format=output_format,
            api_key=api_key
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test Code Generation Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate")
async def generate_test_code(
    process_title: str = Form(...),
    environment_session_id: str = Form(...),
    files: List[UploadFile] = File(...),
    model: Optional[str] = Form("llama3.2:3b"),
    api_key: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    environment_name: Optional[str] = Form(None),
    output_format: Optional[str] = Form("JSON"),
    custom_prompt: Optional[str] = Form(None)
):
    """
    Legacy endpoint for test code generation (backward compatibility)
    Now supports all parameters from /run endpoint
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No source files uploaded")
        
        if not process_title:
            raise HTTPException(status_code=400, detail="Process title is required")
            
        if not environment_session_id:
            raise HTTPException(status_code=400, detail="Environment session ID is required")
        
        # Validate environment_name is provided
        if not environment_name or environment_name.strip() == "":
            raise HTTPException(status_code=400, detail="Test Code Generation Process Name is required")
        
        logger.info(f"Generating test code for process: {process_title}")
        logger.info(f"Using environment session: {environment_session_id}")
        logger.info(f"Uploaded files count: {len(files)}")
        logger.info(f"Using model: {model}")
        logger.info(f"Environment name: {environment_name}")
        logger.info(f"Output format: {output_format}")
        logger.info(f"API key provided: {'Yes' if api_key else 'No'}")
        if api_key:
            logger.info(f"API key preview: {api_key[:15]}...")
        logger.info(f"Session ID: {session_id}")
        
        result = await test_code_service.generate_test_codes(
            process_title=process_title,
            environment_session_id=environment_session_id,
            source_files=files,
            model_name=model,
            api_key=api_key,
            session_id=session_id,
            environment_name=environment_name,
            output_format=output_format,
            custom_prompt=custom_prompt
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test Code Generation Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def run_step(input_data):
    """Backward compatibility için eski fonksiyon"""
    return {"step": "testCodeGeneration", "result": "Test code generation completed."}
