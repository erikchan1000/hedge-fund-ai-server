"""Helper functions for LLM"""

import json
import time
import logging
import threading
from typing import TypeVar, Type, Optional, Any
from pydantic import BaseModel
from utils.progress import progress

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Rate limiting configuration
OPENAI_RATE_LIMIT_DELAY = 1  # seconds between OpenAI API calls
FINANCIAL_API_RATE_LIMIT_DELAY = 1 # seconds between financial API calls

class APIRateLimiter:
    """Thread-safe rate limiter for API calls"""
    _instances = {}
    _lock = threading.Lock()
    
    def __new__(cls, api_type: str):
        if api_type not in cls._instances:
            with cls._lock:
                if api_type not in cls._instances:
                    instance = super(APIRateLimiter, cls).__new__(cls)
                    instance._last_call_time = 0
                    instance._rate_limit_lock = threading.Lock()
                    instance._api_type = api_type
                    instance._delay = OPENAI_RATE_LIMIT_DELAY if api_type == "openai" else FINANCIAL_API_RATE_LIMIT_DELAY
                    cls._instances[api_type] = instance
        return cls._instances[api_type]
    
    def wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits"""
        with self._rate_limit_lock:
            current_time = time.time()
            time_since_last_call = current_time - self._last_call_time
            
            if time_since_last_call < self._delay:
                wait_time = self._delay - time_since_last_call
                logger.debug(f"Rate limiting {self._api_type}: waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
            
            self._last_call_time = time.time()

T = TypeVar('T', bound=BaseModel)

def call_llm(
    prompt: Any,
    model_name: str,
    model_provider: str,
    pydantic_model: Type[T],
    agent_name: Optional[str] = None,
    max_retries: int = 3,
    default_factory = None
) -> T:
    """
    Makes an LLM call with retry logic, handling both JSON supported and non-JSON supported models.
    
    Args:
        prompt: The prompt to send to the LLM
        model_name: Name of the model to use
        model_provider: Provider of the model
        pydantic_model: The Pydantic model class to structure the output
        agent_name: Optional name of the agent for progress updates
        max_retries: Maximum number of retries (default: 3)
        default_factory: Optional factory function to create default response on failure
        
    Returns:
        An instance of the specified Pydantic model
    """
    from llm.models import get_model, get_model_info
    
    model_info = get_model_info(model_name)
    llm = get_model(model_name, model_provider)
    
    # For non-JSON support models, we can use structured output
    if not (model_info and not model_info.has_json_mode()):
        llm = llm.with_structured_output(
            pydantic_model,
            method="json_mode",
        )
    
    # Get the shared rate limiter instance
    rate_limiter = APIRateLimiter("openai")
    
    # Call the LLM with retries
    for attempt in range(max_retries):
        try:
            # Add delay for OpenAI API calls using the shared rate limiter
            if model_provider == "OpenAI":
                rate_limiter.wait_for_rate_limit()
            
            # Call the LLM
            result = llm.invoke(prompt)
            
            # For non-JSON support models, we need to extract and parse the JSON manually
            if model_info and not model_info.has_json_mode():
                parsed_result = extract_json_from_response(result.content)
                if parsed_result:
                    return pydantic_model(**parsed_result)
            else:
                return result
                
        except Exception as e:
            if agent_name:
                progress.update_status(agent_name, None, f"Error - retry {attempt + 1}/{max_retries}")
            
            # If we get a rate limit error, wait longer before retrying
            if "rate_limit_exceeded" in str(e).lower():
                wait_time = OPENAI_RATE_LIMIT_DELAY * (attempt + 1)  # Exponential backoff
                logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds before retry {attempt + 1}...")
                time.sleep(wait_time)
                continue
            
            if attempt == max_retries - 1:
                print(f"Error in LLM call after {max_retries} attempts: {e}")
                # Use default_factory if provided, otherwise create a basic default
                if default_factory:
                    return default_factory()
                return create_default_response(pydantic_model)

    # This should never be reached due to the retry logic above
    return create_default_response(pydantic_model)

def create_default_response(model_class: Type[T]) -> T:
    """Creates a safe default response based on the model's fields."""
    default_values = {}
    for field_name, field in model_class.model_fields.items():
        if field.annotation == str:
            default_values[field_name] = "Error in analysis, using default"
        elif field.annotation == float:
            default_values[field_name] = 0.0
        elif field.annotation == int:
            default_values[field_name] = 0
        elif hasattr(field.annotation, "__origin__") and field.annotation.__origin__ == dict:
            default_values[field_name] = {}
        else:
            # For other types (like Literal), try to use the first allowed value
            if hasattr(field.annotation, "__args__"):
                default_values[field_name] = field.annotation.__args__[0]
            else:
                default_values[field_name] = None
    
    return model_class(**default_values)

def extract_json_from_response(content: str) -> Optional[dict]:
    """Extracts JSON from markdown-formatted response."""
    try:
        json_start = content.find("```json")
        if json_start != -1:
            json_text = content[json_start + 7:]  # Skip past ```json
            json_end = json_text.find("```")
            if json_end != -1:
                json_text = json_text[:json_end].strip()
                return json.loads(json_text)
    except Exception as e:
        print(f"Error extracting JSON from response: {e}")
    return None
