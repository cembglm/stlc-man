from utils.file_handler import FileHandler
from utils.model_client import LLMClient
from utils.text_processor import TextProcessor
from core.prompt_manager import get_base_prompt, save_session_data, get_test_planning_system_suffix
import logging
import os
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('test_planning_service.log')
    ]
)

logger = logging.getLogger("TestPlanningService")
logger.debug("Test log message - If you see this, logging is working!")

class TestPlanningService:
    def __init__(self):
        self.file_handler = FileHandler()
        self.model_client = LLMClient()
        self.text_processor = TextProcessor()
        self.logger = logging.getLogger(__name__)
        self.logger.debug("TestPlanningService initialized")

    def normalize_prompt(self, text):
        return ' '.join(text.strip().split()).lower()

    async def run_test_planning(self, files, model_key=None, custom_prompt=None, session_id=None):
        try:
            self.logger.debug(f"Starting test planning for {len(files)} files with model: {model_key}")
            
            if not files:
                raise ValueError("No files provided for test planning")
                
            file_paths = await self.file_handler.save_files(files)
            self.logger.debug(f"Files saved: {file_paths}")
            
            if not file_paths:
                raise ValueError("Failed to save uploaded files")

            # Dosya içeriklerini ayır: requirement ve kod dosyaları
            requirement_doc_content = ""
            code_files_content = ""
            for path in file_paths:
                filename = os.path.basename(path).lower()
                content = self.file_handler.read_file(path)
                if "requirement" in filename or "spec" in filename or filename.endswith('.md') or filename.endswith('.txt'):
                    requirement_doc_content += content + "\n"
                else:
                    code_files_content += f"\n\n### File: {os.path.basename(path)}\n\n{content}"

            model_client = LLMClient()
            self.logger.info(f"Model key: {model_key}")
            model_name = None
            if model_key:
                model_name = model_client.get_model_identifier(model_key)
                model_client = LLMClient(model_name)
                self.logger.info(f"Using model: {model_name} for test planning")
            else:
                self.logger.info("No model specified, using default model")

            # Bugünün tarihini al
            today = datetime.now().strftime("%Y-%m-%d")

            used_prompt = None
            prompt_source = None
            base_prompt = get_base_prompt("test_planning")
            system_suffix = get_test_planning_system_suffix()

            if custom_prompt:
                used_prompt = custom_prompt
                prompt_source = "custom_parameter"
                self.logger.info("Using custom prompt provided by user in this request")
            else:
                if base_prompt:
                    used_prompt = base_prompt
                    prompt_source = "base_db"
                    self.logger.info("Using base prompt from database")
                else:
                    raise ValueError("No prompt found in database for test_planning process. Please add a prompt to the database.")
            today = datetime.now().strftime("%Y-%m-%d")
            planning_prompt = used_prompt.format(
                code=code_files_content,
                requirement_document=requirement_doc_content,
                today=today
            )

            MAX_TOKENS = 4000
            if len(planning_prompt.split()) > MAX_TOKENS:
                self.logger.debug(f"Token limit exceeded: {len(planning_prompt.split())} > {MAX_TOKENS}")
                chunks = self.text_processor.chunk_text(planning_prompt)
                all_plans = []
                for i, chunk in enumerate(chunks):
                    self.logger.debug(f"Processing chunk {i+1}/{len(chunks)}")
                    plan = await model_client.generate_response(chunk)
                    if plan:
                        all_plans.append(plan)
                final_plan = self._combine_plans(all_plans)
            else:
                self.logger.debug(f"Using single plan. Token count: {len(planning_prompt.split())}")
                final_plan = await model_client.generate_response(planning_prompt)
            
            if not final_plan:
                raise ValueError("Failed to generate test planning")
                
            file_names = [os.path.basename(path) for path in file_paths]
            files_header = "Files analyzed:\n" + "\n".join(file_names)

            edited_prompt = False
            if custom_prompt and base_prompt:
                edited_prompt = (self.normalize_prompt(custom_prompt) != self.normalize_prompt(base_prompt))
            elif custom_prompt and not base_prompt:
                edited_prompt = True
            
            session_data = {
                "session_id": session_id,
                "output": {
                    "files": files_header,
                    "plan": final_plan
                },
                "edited_prompt": edited_prompt,
                "used_prompt": used_prompt,
                "used_model": model_name
            }
            save_session_data(session_data, process_type="test_planning")
            
            for path in file_paths:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception as e:
                    self.logger.warning(f"Failed to remove temporary file {path}: {str(e)}")
            
            return {
                "status": "success",
                "plans": [{
                    "files": files_header,
                    "plan": final_plan
                }],
                "prompt_info": {
                    "source": prompt_source
                },
                "session_id": session_id or "unknown"
            }

        except Exception as e:
            self.logger.error(f"Error in run_test_planning: {str(e)}")
            raise

    def _combine_file_contents(self, file_paths):
        combined_content = ""
        for path in file_paths:
            code_content = self.file_handler.read_file(path)
            combined_content += f"\n\n### File: {os.path.basename(path)}\n\n{code_content}"
        return combined_content

    def _combine_plans(self, plans):
        combined = "\n\n".join(plans)
        return "# Complete Test Planning Summary\n\n" + combined 