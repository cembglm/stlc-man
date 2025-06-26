from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from core.database import get_db
from utils.model_client import LLMClient
from datetime import datetime
import json
import uuid
import logging
import asyncio

logger = logging.getLogger(__name__)

class TestCase(BaseModel):
    ScenarioID: str
    TestCaseID: str
    Title: str
    Description: Optional[str] = None
    Objective: Optional[str] = None

class TestCaseList(BaseModel):
    test_cases: List[TestCase]
    comparison_logs: List[dict] = []
    duplicates: List[dict] = []

async def _query_llm_similarity(case1: TestCase, case2: TestCase, custom_prompt: str = None) -> bool:
    """
    İki TestCase nesnesini LLM'e JSON formatında göndererek benzerlik (is_same) sonucunu döndürür.
    """
    # Create JSON objects
    case1_json = case1.model_dump()
    case2_json = case2.model_dump()

    # Pop the ScenarioID and TestCaseID keys
    case1_json.pop("ScenarioID", None)
    case1_json.pop("TestCaseID", None)
    case2_json.pop("ScenarioID", None)
    case2_json.pop("TestCaseID", None)

    # Use custom prompt if provided, otherwise use default
    if custom_prompt:
        # Replace placeholders in custom prompt with actual test case data
        prompt_text = f"""{custom_prompt}

Below are the two test cases in JSON format:

TestCase1:
{json.dumps(case1_json, indent=2, ensure_ascii=False)}

TestCase2:
{json.dumps(case2_json, indent=2, ensure_ascii=False)}
"""
    else:
        # Default prompt text for Smart Selection using LLM
        prompt_text = f"""
You are given two test cases, each with a certain set of fields:
- Title
- Description
- Objective

You will decide whether these two test cases are "contextually the same" based on the following criteria:

1. If both have the same Title (case-insensitive) OR their Titles are substantially similar in meaning,
2. AND they have either the same or very similar Description and/or Objective,
3. AND they serve essentially the same testing purpose for the same or very closely related scenarios,
4. THEN you should conclude that these two test cases are the same.
5. The order of importance Description > Objective > Title.

Otherwise, they are considered different.

Below are the two test cases in JSON format:

TestCase1:
{json.dumps(case1_json, indent=2, ensure_ascii=False)}

TestCase2:
{json.dumps(case2_json, indent=2, ensure_ascii=False)}

Return your response **only** in valid JSON with the following format:

{{
  "is_same": <true or false>
}}

Where:
- is_same = true if the test cases meet the criteria above
- is_same = false otherwise

Important:
- Do not provide any additional text outside the JSON object.
- Do not explain your reasoning, only provide the final JSON response.
"""

    try:
        # LM Studio API'sine LLMClient ile istek gönder
        llm_client = LLMClient(model_name="llama-3.2-3b-instruct")
        
        # LLMClient'ı kullanarak yanıt al
        response = await llm_client.generate_response(
            prompt=prompt_text.strip(),
            temperature=0.1,  # Consistency için düşük temperature
            max_tokens=1000
        )
        
        if not response:
            logger.error("Empty response from LLM")
            return False
        
        try:
            # JSON parsing ile response'u parse et
            parsed_content = json.loads(response)
            return parsed_content.get("is_same", False)
        except json.JSONDecodeError:
            # Eğer JSON değilse, text içinde "true" veya "false" ara
            response_lower = response.lower()
            if '"is_same": true' in response_lower or '"is_same":true' in response_lower:
                return True
            elif '"is_same": false' in response_lower or '"is_same":false' in response_lower:
                return False
            else:
                logger.error(f"LM Studio response is not valid JSON and doesn't contain expected format: {response}")
                return False
            
    except Exception as e:
        logger.error(f"Error calling LM Studio API via LLMClient: {e}")
        return False

async def smart_select(test_case_list: TestCaseList, custom_prompt: str = None) -> TestCaseList:
    """
    Bu fonksiyon, test_cases listesindeki benzer (duplicate) test case'leri 
    LLM tabanlı karşılaştırma ile ayıklar, unique bir liste döndürür.
    """
    unique_cases = []
    step = 1
    comparison_logs = []
    duplicates = []

    for case in test_case_list.test_cases:
        is_duplicate = False
        for unique_case in unique_cases:
            try:
                comparison_result = await _query_llm_similarity(case, unique_case, custom_prompt)
            except Exception as e:
                logger.warning(f"LLM comparison failed: {e}")
                comparison_result = False

            comparison_logs.append({
                "Step": step,
                "ProcessName": str(uuid.uuid4()),
                "Timestamp": datetime.now().isoformat(),
                "Case1": case.model_dump(),
                "Case2": unique_case.model_dump(),
                "is_same": comparison_result,
            })
            step += 1

            if comparison_result:
                is_duplicate = True
                # Benzer test durumlarını kaydet
                duplicates.append({
                    "DuplicateCase": case.model_dump(),
                    "MatchedWith": unique_case.model_dump()
                })
                break

        if not is_duplicate:
            unique_cases.append(case)

    return TestCaseList(
        test_cases=unique_cases,
        comparison_logs=comparison_logs,
        duplicates=duplicates
    )

class TestCaseOptimizationService:
    def __init__(self):
        self.db = get_db()  # Use synchronous database connection
        self.collection = self.db["session_history"]  # Updated to use session_history collection

    def get_available_process_titles(self) -> List[str]:
        """
        MongoDB'den mevcut process_title değerlerini getir.
        Önce test_case_generation'dan process title'ları kontrol et, sonra test_scenario_generation'dan al.
        """
        try:
            process_titles = set()
            
            # First, get process titles from test_case_generation results
            pipeline_test_cases = [
                {"$match": {"processes.test_case_generation.output.data.test_case_results": {"$exists": True}}},
                {"$unwind": "$processes.test_case_generation.output.data.test_case_results"},
                {"$match": {"processes.test_case_generation.output.data.test_case_results.metadata.selected_process_title": {"$ne": None, "$exists": True}}},
                {"$group": {"_id": "$processes.test_case_generation.output.data.test_case_results.metadata.selected_process_title"}},
                {"$sort": {"_id": 1}}
            ]
            
            cursor = self.collection.aggregate(pipeline_test_cases)
            for doc in cursor:
                if doc["_id"]:
                    process_titles.add(doc["_id"])
            
            # Then, get process titles from test_scenario_generation
            pipeline_scenarios = [
                {"$match": {"processes.test_scenario_generation.process_title": {"$ne": None, "$exists": True}}},
                {"$group": {"_id": "$processes.test_scenario_generation.process_title"}},
                {"$sort": {"_id": 1}}
            ]
            
            cursor = self.collection.aggregate(pipeline_scenarios)
            for doc in cursor:
                if doc["_id"]:
                    process_titles.add(doc["_id"])
            
            # Convert set to sorted list
            return sorted(list(process_titles))
        except Exception as e:
            logger.error(f"Error fetching process titles: {e}")
            return []

    def get_test_cases_by_process_title(self, process_title: str) -> List[Dict[str, Any]]:
        """
        Belirli bir process_title için tüm test case'leri getir.
        Önce test_case_generation sonuçlarını kontrol et, sonra test_scenario_generation'a bak.
        """
        try:
            all_test_cases = []
            
            # First, try to get test cases from test_case_generation (actual generated test cases)
            documents = self.collection.find(
                {"processes.test_case_generation.output.data.test_case_results.metadata.selected_process_title": process_title},
                {"processes.test_case_generation": 1}
            )
            
            for doc in documents:
                test_case_gen_data = doc.get("processes", {}).get("test_case_generation", {})
                output_data = test_case_gen_data.get("output", {}).get("data", {})
                test_case_results = output_data.get("test_case_results", [])
                
                # Iterate through each scenario's test cases
                for result in test_case_results:
                    metadata = result.get("metadata", {})
                    if metadata.get("selected_process_title") == process_title:
                        if result.get("status") == "success" and "test_cases" in result:
                            scenario_id = result.get("scenario_id", "Unknown")
                            test_cases = result.get("test_cases", [])
                            selected_category = metadata.get("selected_category", "Unknown")
                            selected_test_type = metadata.get("selected_test_type", "Unknown")
                            
                            for idx, test_case in enumerate(test_cases):
                                test_case_id = test_case.get("TestCaseID", f"TC_{scenario_id}_{idx}")
                                title = test_case.get("Title", "No Title")
                                description = test_case.get("Description", "No Description")
                                objective = test_case.get("Objective", "No Objective")
                                category = test_case.get("Category", "No Category")
                                
                                all_test_cases.append({
                                    "ScenarioID": scenario_id,
                                    "TestCaseID": test_case_id,
                                    "Title": title,
                                    "Description": description,
                                    "Objective": objective,
                                    "Category": category,
                                    "Priority": test_case.get("Priority", "Medium"),
                                    "Prerequisites": test_case.get("Prerequisites", []),
                                    "TestSteps": test_case.get("TestSteps", []),
                                    "ExpectedResults": test_case.get("ExpectedResults", ""),
                                    "TestData": test_case.get("TestData", ""),
                                    "Comments": test_case.get("Comments", ""),
                                    "SelectedCategory": selected_category,
                                    "SelectedTestType": selected_test_type,
                                    "unique_key": f"{test_case_id}_{selected_category}_{selected_test_type}"
                                })
            
            # If no test cases found from test_case_generation, fallback to test_scenario_generation (scenarios only)
            if not all_test_cases:
                documents = self.collection.find(
                    {"processes.test_scenario_generation.process_title": process_title},
                    {"processes.test_scenario_generation": 1}
                )
                
                for doc in documents:
                    test_generation_data = doc.get("processes", {}).get("test_scenario_generation", {})
                    test_scenarios = test_generation_data.get("output", {}).get("test_scenarios", {})
                    selected_category = test_generation_data.get("selected_category", "Unknown")
                    selected_test_type = test_generation_data.get("selected_test_type", "Unknown")
                    
                    # Test scenarios yapısını kontrol et
                    scenarios_list = []
                    if isinstance(test_scenarios, dict):
                        scenarios_list = test_scenarios.get("TestScenarios", [])
                    elif isinstance(test_scenarios, list):
                        scenarios_list = test_scenarios
                    
                    for idx, scenario in enumerate(scenarios_list):
                        scenario_id = scenario.get("ScenarioID", f"Scenario_{idx}")
                        title = scenario.get("Title", "No Title")
                        description = scenario.get("Description", "No Description")
                        objective = scenario.get("Objective", "No Objective")
                        category = scenario.get("Category", "No Category")
                        comments = scenario.get("Comments", "No Comments")
                        
                        all_test_cases.append({
                            "ScenarioID": scenario_id,
                            "TestCaseID": scenario_id,  # Use ScenarioID as TestCaseID for scenarios
                            "Title": title,
                            "Description": description,
                            "Objective": objective,
                            "Category": category,
                            "Comments": comments,
                            "SelectedCategory": selected_category,
                            "SelectedTestType": selected_test_type,
                            "unique_key": f"{scenario_id}_{selected_category}_{selected_test_type}"
                        })
            
            logger.info(f"Found {len(all_test_cases)} test cases for process_title: {process_title}")
            return all_test_cases
        except Exception as e:
            logger.error(f"Error fetching test cases for process_title {process_title}: {e}")
            return []

    async def run_smart_selection(self, selected_test_cases: List[Dict[str, Any]], custom_prompt: str = None) -> Dict[str, Any]:
        """
        Seçilen test case'ler üzerinde smart selection işlemini çalıştır.
        """
        try:
            # Pydantic modeline dönüştür
            valid_data = []
            for item in selected_test_cases:
                try:
                    test_case = TestCase(
                        ScenarioID=item.get("ScenarioID", ""),
                        TestCaseID=item.get("TestCaseID", ""),
                        Title=item.get("Title", ""),
                        Description=item.get("Description"),
                        Objective=item.get("Objective")
                    )
                    valid_data.append(test_case)
                except Exception as e:
                    logger.warning(f"Skipping invalid test case: {item}. Error: {e}")

            if not valid_data:
                return {
                    "success": False,
                    "message": "No valid test cases to process",
                    "data": {}
                }

            # Smart selection işlemini çalıştır
            test_case_list = TestCaseList(test_cases=valid_data)
            unique_test_cases = await smart_select(test_case_list, custom_prompt)

            results = {
                "unique_test_cases": [case.model_dump() for case in unique_test_cases.test_cases],
                "similar_test_cases": unique_test_cases.duplicates,
                "comparison_logs": unique_test_cases.comparison_logs,
            }

            return {
                "success": True,
                "message": "Smart selection completed successfully",
                "data": results
            }

        except Exception as e:
            logger.error(f"Error running smart selection: {e}")
            return {
                "success": False,
                "message": f"Error running smart selection: {str(e)}",                "data": {}
            }

    def save_optimization_results(self, process_title: str, results: Dict[str, Any]) -> bool:
        """
        Optimization sonuçlarını MongoDB'ye kaydet.
        """
        try:
            # Optimization sonuçlarını ayrı bir koleksiyonda sakla
            optimization_collection = self.db["test_case_optimizations"]
            
            document = {
                "process_title": process_title,
                "optimization_results": results,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Upsert operation - eğer varsa güncelle, yoksa yeni oluştur
            optimization_collection.update_one(
                {"process_title": process_title},
                {"$set": document},
                upsert=True
            )
            
            return True
        except Exception as e:
            logger.error(f"Error saving optimization results: {e}")
            return False

    def get_optimization_results(self, process_title: str) -> Optional[Dict[str, Any]]:
        """
        Belirli bir process_title için kaydedilmiş optimization sonuçlarını getir.
        """
        try:
            optimization_collection = self.db["test_case_optimizations"]
            result = optimization_collection.find_one({"process_title": process_title})
            
            if result:
                return result.get("optimization_results")
            return None
        except Exception as e:
            logger.error(f"Error fetching optimization results: {e}")
            return None
