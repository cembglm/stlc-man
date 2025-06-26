from utils.file_handler import FileHandler
from utils.model_client import LLMClient
from utils.text_processor import TextProcessor
from core.prompt_manager import get_base_prompt, get_requirement_analysis_system_suffix, save_session_data
import logging
import os
from datetime import datetime

logger = logging.getLogger("RequirementAnalysisService")

class RequirementAnalysisService:
    def __init__(self):
        self.file_handler = FileHandler()
        self.model_client = LLMClient()
        self.text_processor = TextProcessor()
        self.logger = logging.getLogger(__name__)

    def normalize_prompt(self, text):
        return ' '.join(text.strip().split()).lower()

    async def run_requirement_analysis(self, files, types=None, model_key=None, custom_prompt=None, session_id=None):
        try:
            self.logger.debug(f"Starting requirement analysis for {len(files)} files with model: {model_key}")
            if not files:
                raise ValueError("No files provided for analysis")

            file_paths = await self.file_handler.save_files(files)
            self.logger.debug(f"Files saved: {file_paths}")
            if not file_paths:
                raise ValueError("Failed to save uploaded files")

            # types zorunlu, eksik veya uzunluklar eşit değilse hata fırlat
            if types is None or len(types) != len(file_paths):
                raise ValueError("Hem Source Code hem de Requirement Document dosyası yüklenmeli ve types parametresi eksiksiz olmalı!")

            # Dosya tiplerine göre içerikleri ayır
            requirement_doc_content = ""
            code_files_content = ""
            for path, file_type in zip(file_paths, types):
                content = self.file_handler.read_file(path)
                if file_type == 'Requirement Document':
                    requirement_doc_content += content + "\n"
                else:
                    code_files_content += f"\n\n### File: {os.path.basename(path)}\n\n{content}"

            model_client = LLMClient()
            model_name = None
            if model_key:
                model_name = model_client.get_model_identifier(model_key)
                model_client = LLMClient(model_name)
                self.logger.info(f"Using model: {model_name} for analysis")
            else:
                self.logger.info("No model specified, using default model")

            used_prompt = None
            prompt_source = None
            base_prompt = get_base_prompt("requirement_analysis")
            system_suffix = get_requirement_analysis_system_suffix()

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
                    raise ValueError("No prompt found in database for requirement_analysis process. Please add a prompt to the database.")

            # Promptu oluştururken doğru alanları kullan
            analysis_prompt = used_prompt + system_suffix
            analysis_prompt = analysis_prompt.format(
                code=code_files_content,
                requirement_document=requirement_doc_content
            )

            MAX_TOKENS = 4000
            if len(analysis_prompt.split()) > MAX_TOKENS:
                self.logger.debug(f"Token limit exceeded: {len(analysis_prompt.split())} > {MAX_TOKENS}")
                chunks = self.text_processor.chunk_text(analysis_prompt)
                all_results = []
                for i, chunk in enumerate(chunks):
                    self.logger.debug(f"Processing chunk {i+1}/{len(chunks)}")
                    result = await model_client.generate_response(chunk)
                    if result:
                        all_results.append(result)
                final_result = self._combine_results(all_results)
            else:
                self.logger.debug(f"Using single analysis. Token count: {len(analysis_prompt.split())}")
                final_result = await model_client.generate_response(analysis_prompt)

            if not final_result:
                raise ValueError("Failed to generate requirement analysis")

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
                    "analysis": final_result
                },
                "edited_prompt": edited_prompt,
                "used_prompt": used_prompt,
                "used_model": model_name
            }
            save_session_data(session_data, process_type="requirement_analysis")

            for path in file_paths:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception as e:
                    self.logger.warning(f"Failed to remove temporary file {path}: {str(e)}")

            return {
                "status": "success",
                "analysis": [{
                    "files": files_header,
                    "result": final_result
                }],
                "prompt_info": {
                    "source": prompt_source
                },
                "session_id": session_id or "unknown"
            }

        except Exception as e:
            self.logger.error(f"Error in run_requirement_analysis: {str(e)}")
            raise

    def _combine_file_contents(self, file_paths):
        combined_content = ""
        for path in file_paths:
            code_content = self.file_handler.read_file(path)
            combined_content += f"\n\n### File: {os.path.basename(path)}\n\n{code_content}"
        return combined_content

    def _combine_results(self, results):
        combined = "\n\n".join(results)
        return "# Complete Requirement Analysis Summary\n\n" + combined 