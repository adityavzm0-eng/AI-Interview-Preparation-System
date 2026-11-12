"""
Gemini API client module.
Handles initialization, auto-detection, structured prompting, model fallback,
rate limit handling, connection testing, and structured JSON parsing.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from config import GEMINI_API_KEY, DEFAULT_GEMINI_MODEL, OPENAI_API_KEY, BASE_DIR
from utils.helpers import extract_json_from_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Available models in priority order
CANDIDATE_GEMINI_MODELS = [
    DEFAULT_GEMINI_MODEL,
    "gemini-1.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-pro",
    "gemini-1.0-pro"
]


def detect_provider(key: str) -> str:
    """Auto-detects API provider based on key prefix pattern."""
    clean_key = key.strip()
    if clean_key.startswith("AIzaSy"):
        return "gemini"
    if clean_key.startswith("sk-"):
        return "openai"
    return "gemini"


def sanitize_key(key: str) -> str:
    """Removes surrounding quotes, spaces, and accidental label text."""
    if not key:
        return ""
    clean = key.strip().strip("'\"")
    # Remove accidental prefix like "api_key = " or "key: "
    clean = re.sub(r"^(?:api[_-]?key\s*[:=]\s*)", "", clean, flags=re.IGNORECASE).strip()
    return clean


class GeminiClient:
    """Manages communication with Google Gemini API and optional OpenAI fallback."""

    def __init__(self, api_key: Optional[str] = None):
        raw_gemini = api_key or GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        raw_openai = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
        
        self.api_key = sanitize_key(raw_gemini)
        self.openai_key = sanitize_key(raw_openai)
        
        # Resolve active provider
        if self.api_key.startswith("sk-") and not self.openai_key:
            self.openai_key = self.api_key
            self.api_key = ""
            self._provider = "openai"
        elif self.api_key:
            self._provider = "gemini"
        elif self.openai_key:
            self._provider = "openai"
        else:
            self._provider = "none"

    def is_configured(self) -> bool:
        """Checks if a valid API key is present."""
        return bool(self.api_key) or bool(self.openai_key)

    def set_api_key(self, key: str, provider: str = "auto", persist: bool = True):
        """Dynamically updates the API key from session state / UI."""
        clean = sanitize_key(key)
        
        if provider == "auto":
            provider = detect_provider(clean)

        if provider == "gemini":
            self.api_key = clean
            self._provider = "gemini"
            env_var = "GEMINI_API_KEY"
        else:
            self.openai_key = clean
            self._provider = "openai"
            env_var = "OPENAI_API_KEY"

        if persist:
            self._persist_to_env(env_var, clean)

    def _persist_to_env(self, var_name: str, value: str):
        """Persists the API key to .env file for future reloads."""
        try:
            env_file = BASE_DIR / ".env"
            lines = []
            found = False
            if env_file.exists():
                with open(env_file, "r") as f:
                    for line in f:
                        if line.startswith(f"{var_name}="):
                            lines.append(f"{var_name}={value}\n")
                            found = True
                        else:
                            lines.append(line)
            if not found:
                lines.append(f"{var_name}={value}\n")
            with open(env_file, "w") as f:
                f.writelines(lines)
            os.environ[var_name] = value
        except Exception as ex:
            logger.warning(f"Could not write to .env: {ex}")

    def get_provider(self) -> str:
        return self._provider

    def test_connection(self) -> Tuple[bool, str]:
        """Runs a minimal test prompt to verify API key validity."""
        if not self.is_configured():
            return False, "No API key configured."
        
        test_prompt = "Say 'OK' and nothing else."
        success, text, err = self.generate_content(test_prompt, expect_json=False)
        if success:
            return True, f"Connection successful with {self._provider.upper()} API!"
        return False, err

    def generate_content(self, prompt: str, system_instruction: Optional[str] = None, expect_json: bool = True) -> Tuple[bool, Any, str]:
        """
        Sends prompt to Gemini (or OpenAI if configured).
        Returns:
            (success: bool, data_or_text: Any, error_message: str)
        """
        if not self.is_configured():
            return (
                False,
                None,
                "API key is not configured. Please add your free Google Gemini API key at https://aistudio.google.com/app/apikey or configure it in the sidebar."
            )

        # Primary: Google Gemini API
        if self._provider == "gemini" and self.api_key:
            return self._call_gemini(prompt, system_instruction, expect_json)
        
        # Secondary: OpenAI API
        if self._provider == "openai" and self.openai_key:
            return self._call_openai(prompt, system_instruction, expect_json)

        # Fallbacks
        if self.api_key:
            return self._call_gemini(prompt, system_instruction, expect_json)
        if self.openai_key:
            return self._call_openai(prompt, system_instruction, expect_json)

        return False, None, "No active API provider found."

    def _call_gemini(self, prompt: str, system_instruction: Optional[str], expect_json: bool) -> Tuple[bool, Any, str]:
        """Calls Google Gemini using google-genai or google-generativeai."""
        last_error = ""

        # Strategy 1: Modern google.genai client
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=self.api_key)
            for model_name in CANDIDATE_GEMINI_MODELS:
                try:
                    config = types.GenerateContentConfig(
                        temperature=0.3 if expect_json else 0.7,
                        system_instruction=system_instruction if system_instruction else None,
                        response_mime_type="application/json" if expect_json else "text/plain"
                    )
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config
                    )
                    raw_text = response.text or ""
                    if expect_json:
                        parsed = extract_json_from_text(raw_text)
                        if parsed is not None:
                            return True, parsed, ""
                    else:
                        return True, raw_text, ""
                except Exception as ex:
                    last_error = str(ex)
                    logger.warning(f"google.genai call with {model_name} failed: {ex}")
                    continue
        except ImportError:
            pass
        except Exception as e:
            last_error = str(e)

        # Strategy 2: Legacy google.generativeai
        try:
            import google.generativeai as genai_legacy
            genai_legacy.configure(api_key=self.api_key)

            for model_name in CANDIDATE_GEMINI_MODELS:
                try:
                    model = genai_legacy.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_instruction
                    )
                    generation_config = {"temperature": 0.3 if expect_json else 0.7}
                    response = model.generate_content(prompt, generation_config=generation_config)
                    raw_text = response.text or ""

                    if expect_json:
                        parsed = extract_json_from_text(raw_text)
                        if parsed is not None:
                            return True, parsed, ""
                    else:
                        return True, raw_text, ""
                except Exception as ex:
                    last_error = str(ex)
                    logger.warning(f"google.generativeai call with {model_name} failed: {ex}")
                    continue
        except ImportError:
            pass
        except Exception as e:
            last_error = str(e)

        # Strategy 3: Direct HTTP REST request to Gemini v1beta endpoint
        try:
            import requests
            headers = {"Content-Type": "application/json"}
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            
            full_prompt = (f"System Instruction: {system_instruction}\n\n" if system_instruction else "") + prompt
            payload = {
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {"temperature": 0.3 if expect_json else 0.7}
            }
            res = requests.post(url, headers=headers, json=payload, timeout=25)
            if res.status_code == 200:
                data = res.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                if expect_json:
                    parsed = extract_json_from_text(text)
                    if parsed is not None:
                        return True, parsed, ""
                else:
                    return True, text, ""
            else:
                last_error = f"HTTP {res.status_code}: {res.text}"
        except Exception as ex:
            last_error = f"REST request failed: {ex}"

        clean_msg = self._format_error(last_error)
        return False, None, clean_msg

    def _call_openai(self, prompt: str, system_instruction: Optional[str], expect_json: bool) -> Tuple[bool, Any, str]:
        """OpenAI API call."""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_key)
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            kwargs = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "temperature": 0.3 if expect_json else 0.7
            }
            if expect_json:
                kwargs["response_format"] = {"type": "json_object"}

            response = client.chat.completions.create(**kwargs)
            text = response.choices[0].message.content or ""
            if expect_json:
                parsed = extract_json_from_text(text)
                if parsed is not None:
                    return True, parsed, ""
            return True, text, ""
        except Exception as ex:
            raw = str(ex)
            if "401" in raw or "Incorrect API key" in raw or "invalid_api_key" in raw:
                return False, None, (
                    "OpenAI Error: Incorrect or expired API key (401 Unauthorized).\n"
                    "👉 Tips:\n"
                    "1. Get a 100% FREE Google Gemini API key at: https://aistudio.google.com/app/apikey (Recommended, no credit card required!)\n"
                    "2. Or verify your OpenAI key has active billing credits at: https://platform.openai.com/account/billing"
                )
            if "quota" in raw or "429" in raw:
                return False, None, "OpenAI Error: You exceeded your current quota or rate limit. Check your billing plan."
            return False, None, f"OpenAI API Error: {raw}"

    def _format_error(self, raw_error: str) -> str:
        """Converts raw exception into a clean, constructive user notice."""
        lower = raw_error.lower()
        if "quota" in lower or "429" in lower or "resource_exhausted" in lower:
            return "Gemini API Quota Exceeded. Please check your Google AI Studio plan or retry in a few moments."
        if "invalid" in lower and "key" in lower or "api_key_invalid" in lower or "400" in lower or "permission_denied" in lower:
            return (
                "Invalid Google Gemini API Key.\n"
                "👉 Get your free key instantly at https://aistudio.google.com/app/apikey and paste it into the sidebar."
            )
        if "timeout" in lower or "connection" in lower:
            return "Connection to Google Gemini API timed out. Please check your internet connectivity."
        return f"API Error: {raw_error[:250]}"
