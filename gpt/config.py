# config.py
import os
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class Config:
    """Central configuration manager with validation and fail-fast behavior."""
    
    def __init__(self):
        """Initialize configuration with environment variables."""
        # Load environment variables once at startup
        load_dotenv()
        
        # Core API Keys
        self.groq_api_key = self._get_required_env("GROQ_API_KEY")
        self.picovoice_access_key = self._get_required_env("PICOVOICE_ACCESS_KEY")
        
        # Paths and files
        self.wakeword_path = self._get_env("WAKEWORD_PATH", 
            default=r"assets\selina_en_windows_v3_0_0.ppn")
        
        # LLM Configuration
        self.llm_model = self._get_env("LLM_MODEL", default="llama-3.1-70b-versatile")
        self.llm_fallback_model = self._get_env("LLM_FALLBACK_MODEL", default="llama3-8b-8192")
        self.llm_temperature = float(self._get_env("LLM_TEMPERATURE", default="0.7"))
        self.llm_max_tokens = int(self._get_env("LLM_MAX_TOKENS", default="150"))
        
        # Audio Configuration
        self.stt_timeout = float(self._get_env("STT_TIMEOUT", default="5.0"))
        self.stt_phrase_limit = float(self._get_env("STT_PHRASE_LIMIT", default="10.0"))
        self.wake_word_sensitivity = float(self._get_env("WAKE_WORD_SENSITIVITY", default="0.5"))
        
        # Processing Configuration
        self.processing_debounce_time = float(self._get_env("PROCESSING_DEBOUNCE_TIME", default="1.0"))
        self.max_retry_attempts = int(self._get_env("MAX_RETRY_ATTEMPTS", default="3"))
        
        # Validate configuration
        self._validate_config()
        
    def _get_required_env(self, key: str) -> str:
        """Get required environment variable or raise error."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
        
    def _get_env(self, key: str, default: str) -> str:
        """Get environment variable with default fallback."""
        return os.getenv(key, default)
        
    def _validate_config(self) -> None:
        """Validate configuration values and file paths."""
        # Validate wake word file exists
        if not os.path.exists(self.wakeword_path):
            raise FileNotFoundError(f"Wake word file not found: {self.wakeword_path}")
            
        # Validate numeric ranges
        if not 0.0 <= self.llm_temperature <= 2.0:
            raise ValueError(f"LLM temperature must be between 0.0 and 2.0, got {self.llm_temperature}")
            
        if not 0.0 < self.wake_word_sensitivity <= 1.0:
            raise ValueError(f"Wake word sensitivity must be between 0.0 and 1.0, got {self.wake_word_sensitivity}")
            
        if self.llm_max_tokens <= 0:
            raise ValueError(f"LLM max tokens must be positive, got {self.llm_max_tokens}")
            
        logger.info("Configuration validated successfully")
        
    def get_system_prompt(self) -> str:
        """Get the system prompt for the LLM."""
        return (
            "You are Zoya, a helpful desktop voice assistant. "
            "Your responses should be concise, clear, and suitable for text-to-speech. "
            "Summarize complex information into core details. "
            "Keep responses under 2-3 sentences when possible. "
            "Be friendly but direct. Avoid technical jargon unless specifically asked. "
            "If you need to provide detailed information, organize it with clear main points."
        )
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for logging."""
        return {
            "llm_model": self.llm_model,
            "llm_fallback_model": self.llm_fallback_model,
            "llm_temperature": self.llm_temperature,
            "llm_max_tokens": self.llm_max_tokens,
            "stt_timeout": self.stt_timeout,
            "stt_phrase_limit": self.stt_phrase_limit,
            "wake_word_sensitivity": self.wake_word_sensitivity,
            "processing_debounce_time": self.processing_debounce_time,
            "max_retry_attempts": self.max_retry_attempts,
            "wakeword_path": self.wakeword_path
        }

# Global configuration instance
config = None

def get_config() -> Config:
    """Get global configuration instance."""
    global config
    if config is None:
        config = Config()
    return config

def validate_config() -> bool:
    """Validate configuration at startup."""
    try:
        get_config()
        return True
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return False