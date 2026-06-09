import json
import os
import re
import logging
from typing import Any, Dict, List, Optional
import google.generativeai as genai
from pydantic import BaseModel, Field, ValidationError
from typing_extensions import Literal

# Configure logging
logger = logging.getLogger("CodeReviewer.GeminiClient")

class Finding(BaseModel):
    file: str
    line: int
    severity: Literal["High", "Medium", "Low"]
    category: Literal["SOLID Principles", "Null Handling", "Async Correctness"]
    issue: str
    suggestion: str

class ReviewResult(BaseModel):
    findings: List[Finding]


class GeminiCodeReviewer:
    """Client for interacting with Google's Gemini AI to analyze C# code."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        # Validate and retrieve the API key
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set.")
        
        # Configure the Google Generative AI SDK
        genai.configure(api_key=self.api_key)
        
        # Determine the model name
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        logger.info(f"Initialized Gemini client with model: {self.model_name}")
        
        # Initialize the generative model
        self.model = genai.GenerativeModel(self.model_name)
        
        # Load the prompt template
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Loads the prompt template from prompts/review_prompt.txt."""
        # Find the prompt path relative to the current file (which is in the agent/ directory)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(current_dir, "..", "prompts", "review_prompt.txt")
        
        # Fallback to local execution directory if parent folder search fails
        if not os.path.exists(prompt_path):
            prompt_path = os.path.join("prompts", "review_prompt.txt")
            
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Prompt template file not found at: {prompt_path}")
            raise RuntimeError(f"Could not load review_prompt.txt at {prompt_path}")

    def _clean_json_response(self, text: str) -> str:
        """Cleans and extracts JSON text from raw AI response."""
        text = text.strip()
        # Attempt to strip markdown code blocks (e.g. ```json ... ```)
        markdown_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if markdown_match:
            text = markdown_match.group(1).strip()
        return text

    def analyze_file(self, filename: str, content: str) -> Dict[str, Any]:
        """
        Sends the C# file content to Gemini AI, validates the structured JSON output,
        and implements a self-correction retry loop if the output is invalid.
        """
        # Format the system prompt with target file details
        prompt = self.prompt_template.replace("{filename}", filename).replace("{content}", content)
        
        max_retries = 2
        attempts = 0
        
        # Configure generation settings to request JSON
        generation_config = {
            "response_mime_type": "application/json",
            "temperature": 0.1,  # Low temperature for deterministic analysis
        }
        
        last_response_text = ""
        error_msg = ""
        
        # Loop for agentic self-correction
        while attempts <= max_retries:
            attempts += 1
            logger.info(f"Analyzing {filename} - Attempt {attempts}/{max_retries + 1}")
            
            try:
                if attempts == 1:
                    # Initial prompt
                    response = self.model.generate_content(
                        prompt, 
                        generation_config=generation_config
                    )
                else:
                    # Self-correction prompt: send the previous context + error message
                    correction_prompt = (
                        f"Your previous JSON output was invalid.\n"
                        f"Error: {error_msg}\n"
                        f"Previous Response:\n{last_response_text}\n\n"
                        f"Please correct the JSON response. Ensure it matches the JSON schema and has NO syntax errors."
                    )
                    
                    # We can use a chat context or just generate from prompt + correction context
                    # To keep it simple, we generate content combining the original prompt and correction instructions
                    combined_prompt = f"{prompt}\n\n=== REPAIR REQUEST ===\n{correction_prompt}"
                    response = self.model.generate_content(
                        combined_prompt,
                        generation_config=generation_config
                    )
                
                last_response_text = response.text
                cleaned_text = self._clean_json_response(last_response_text)
                
                # Try loading the text as JSON
                parsed_json = json.loads(cleaned_text)
                
                # Validate using Pydantic
                validated_data = ReviewResult.model_validate(parsed_json)
                
                logger.info(f"Successfully analyzed {filename} on attempt {attempts}.")
                # Return the validated model serialized back to standard dict
                return validated_data.model_dump()
                
            except (json.JSONDecodeError, ValidationError) as e:
                error_msg = str(e)
                logger.warning(
                    f"Validation failed on attempt {attempts} for {filename}. "
                    f"Error: {error_msg}"
                )
                
                if attempts > max_retries:
                    logger.error(
                        f"Failed to get valid JSON from Gemini after {attempts} attempts for {filename}."
                    )
                    # Return safe fallback with empty findings list
                    return {"findings": []}
            except Exception as e:
                logger.error(f"Unexpected error during Gemini API call for {filename}: {str(e)}")
                # Fail fast on unexpected API errors (e.g., Auth, Rate Limit) to let caller handle it
                raise e
        
        return {"findings": []}
