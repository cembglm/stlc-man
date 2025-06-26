"""
environment_setup.py
--------------------
STLC'nin Environment Setup adımına ait işlemleri yönetir.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from services.environment_setup_service import EnvironmentSetupService
import logging
from typing import Optional, List

router = APIRouter()
logger = logging.getLogger("environment_setup")
env_setup_service = EnvironmentSetupService()

@router.post("/run")
async def process_environment_setup(
    files: List[UploadFile] = File(...),
    types: List[str] = Form(...),
    model: Optional[str] = Form(None),
    custom_prompt: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None)
):
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files uploaded.")
        logger.info(f"Environment setup requested with model: {model} ve session_id: {session_id}")
        results = await env_setup_service.run_environment_setup(files, types, model, custom_prompt, session_id)
        return results
    except Exception as e:
        logger.error(f"Environment Setup Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
