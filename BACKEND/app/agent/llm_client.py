import json
import logging
import re
import time
from typing import Dict, Any, List, Optional, Tuple
from groq import Groq, APIError
from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for cloud-based LLM inference.
    Primary provider: Google Gemini (gemini-2.5-flash)
    Fallback provider: Groq (qwen/qwen3.8-27b)
    Automatically rotates to Groq when Gemini hits rate limits or fails.
    """

    # ─────────────────────────── availability ──────────────────────────────

    @classmethod
    def _gemini_key(cls) -> str:
        key = getattr(settings, "GEMINI_API_KEY", "").strip()
        return key if (key and not key.startswith("YOUR_")) else ""

    @classmethod
    def _groq_key(cls) -> str:
        key = getattr(settings, "GROQ_API_KEY", "").strip()
        return key if (key and not key.startswith("YOUR_")) else ""

    @classmethod
    def is_available(cls) -> bool:
        return bool(cls._gemini_key() or cls._groq_key())

    # ─────────────────────────── public API ────────────────────────────────

    @classmethod
    def classify_intent(cls, query: str) -> str:
        """
        Classify the user query into a fixed set of intents using the LLM.
        """
        system_prompt = (
            "Classify the user's query into exactly ONE of the following intents: "
            "ATTENDANCE, EXAMS, FEES, TIMETABLE, MARKS, CURRICULUM, LIBRARY, FACULTY, KNOWLEDGE_BASE, GENERAL, "
            "POLICIES, CIRCULARS, CALENDAR, CLUBS, LOST_AND_FOUND, BOOKINGS, SERVICES, MAP, EVENTS, HOSTEL, MARKETPLACE, "
            "CAREER, GAMIFICATION, TRANSPORT, ALUMNI, WELLNESS, POLLING. "
            "Respond with ONLY the intent name in uppercase, and nothing else."
        )

        reply = cls._send_chat(
            messages=[{"role": "user", "content": cls.redact_pii_text(query)}],
            system_prompt=system_prompt,
        )

        if reply:
            reply = reply.strip().upper()
            valid_intents = [
                "ATTENDANCE", "EXAMS", "FEES", "TIMETABLE", "MARKS",
                "CURRICULUM", "LIBRARY", "FACULTY", "KNOWLEDGE_BASE", "GENERAL",
                "POLICIES", "CIRCULARS", "CALENDAR", "CLUBS", "LOST_AND_FOUND",
                "BOOKINGS", "SERVICES", "MAP", "EVENTS", "HOSTEL", "MARKETPLACE",
                "CAREER", "GAMIFICATION", "TRANSPORT", "ALUMNI", "WELLNESS", "POLLING"
            ]
            for intent in valid_intents:
                if intent in reply:
                    return intent
        return "GENERAL"

    @classmethod
    def redact_pii_text(cls, text: str) -> str:
        """
        Scrubs student personally identifiable information (PII) before sending to external cloud LLMs:
        - University roll numbers (e.g. 24CSE001, 23ECE045, 21IT123)
        - Phone numbers (10 digits with optional +91, 91, or 0 prefix)
        - Email addresses (e.g. student email addresses)
        """
        if not text:
            return text

        # 1. Roll numbers (e.g., 24CSE001, 22IT012, etc.)
        cleaned = re.sub(r"\b\d{2}[A-Za-z]{2,5}\d{3,4}\b", "[Redacted Roll No]", text, flags=re.IGNORECASE)

        # 2. Email addresses
        cleaned = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[Redacted Email]", cleaned)

        # 3. Phone numbers (10-digit Indian numbers with optional country/trunk code)
        cleaned = re.sub(r"(?:\+91[\-\s]?|91[\-\s]?|0)?[6-9]\d{4}[\-\s]?\d{5}\b", "[Redacted Phone]", cleaned)
        cleaned = re.sub(r"(?:\+91[\-\s]?|91[\-\s]?|0)?[6-9]\d{9}\b", "[Redacted Phone]", cleaned)

        return cleaned

    @classmethod
    def chat_with_history(
        cls,
        system_prompt: str,
        history: List[Dict[str, Any]],
        user_prompt: str,
        model: Optional[str] = None,
        max_history_turns: int = 4,
        language: str = "en",
    ) -> Tuple[Optional[str], str, str]:
        """
        Generate a multi-turn contextual response.
        Returns (response_text, provider_name, model_name).
        """
        messages = []
        recent_turns = history[-max_history_turns:] if len(history) > max_history_turns else history

        for turn in recent_turns:
            role = "user" if turn.get("sender_role") == "STUDENT" else "assistant"
            content = cls.redact_pii_text(turn.get("content", ""))
            if len(content) > 800:
                content = content[:800] + "..."
            if content:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": cls.redact_pii_text(user_prompt)})

        res, provider, model_used = cls._send_chat_with_provider(messages, system_prompt=system_prompt)
        if res:
            return res, provider, model_used

        return None, "mock", "deterministic-fallback"

    # ─────────────────────────── routing logic ─────────────────────────────

    @classmethod
    def _send_chat(
        cls,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> Optional[str]:
        """Send chat, returns text only."""
        result, _, _ = cls._send_chat_with_provider(messages, system_prompt)
        return result

    @classmethod
    def _send_chat_with_provider(
        cls,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> Tuple[Optional[str], str, str]:
        messages = [{"role": m["role"], "content": cls.redact_pii_text(m["content"])} for m in messages]
        if system_prompt:
            system_prompt = cls.redact_pii_text(system_prompt)
        """
        Try Gemini first; fall back to Groq on failure or rate limit.
        Returns (text, provider, model).
        """
        # 1. Try Gemini (primary)
        gemini_key = cls._gemini_key()
        if gemini_key:
            result = cls._send_gemini_chat(messages, system_prompt, gemini_key)
            if result is not None:
                model_used = getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash")
                logger.info(f"Response served by Gemini ({model_used})")
                return result, "gemini", model_used
            logger.warning("Gemini failed or rate-limited — falling back to Groq")

        # 2. Fall back to Groq
        groq_key = cls._groq_key()
        if groq_key:
            result = cls._send_groq_chat(messages, system_prompt, groq_key)
            if result is not None:
                model_used = getattr(settings, "GROQ_MODEL", "qwen/qwen3.8-27b")
                logger.info(f"Response served by Groq fallback ({model_used})")
                return result, "groq", model_used

        return None, "none", "none"

    # ─────────────────────────── Gemini provider ───────────────────────────

    @classmethod
    def _send_gemini_chat(
        cls,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str],
        api_key: str,
    ) -> Optional[str]:
        """Call Google Gemini API. Returns cleaned text or None on error."""
        try:
            from google import genai

            model_name = getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash")

            contents = []
            for msg in messages:
                role = "user" if msg["role"] == "user" else "model"
                clean_msg = cls.redact_pii_text(msg["content"])
                contents.append(
                    genai.types.Content(
                        role=role,
                        parts=[genai.types.Part(text=clean_msg)],
                    )
                )

            config_kwargs: Dict[str, Any] = {
                "max_output_tokens": 1500,
                "temperature": 0.4,
            }
            if system_prompt:
                config_kwargs["system_instruction"] = cls.redact_pii_text(system_prompt)

            client = genai.Client(api_key=api_key)
            
            if len(contents) > 1:
                history = contents[:-1]
                last_message = contents[-1].parts
            elif len(contents) == 1:
                history = None
                last_message = contents[0].parts
            else:
                history = None
                last_message = ""

            chat = client.chats.create(
                model=model_name,
                history=history,
                config=genai.types.GenerateContentConfig(**config_kwargs),
            )
            response = chat.send_message(last_message)

            raw_text = response.text if response and response.text else None
            if not raw_text:
                logger.warning("Gemini returned empty response")
                return None

            cleaned = cls.clean_latex_formatting(raw_text)
            if not cleaned or not cleaned.strip():
                cleaned = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
            return cleaned if cleaned else None

        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                logger.warning(f"Gemini rate limit hit: {e}")
            elif "API_KEY_INVALID" in err_str or "INVALID_ARGUMENT" in err_str:
                logger.error(f"Gemini API key error: {e}")
            else:
                logger.warning(f"Gemini request failed: {type(e).__name__}: {e}")
            return None

    # ─────────────────────────── Groq provider ─────────────────────────────

    @classmethod
    def _send_groq_chat(
        cls,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str],
        api_key: str,
    ) -> Optional[str]:
        """Call Groq API. Returns cleaned text or None on error."""
        candidate_model = getattr(settings, "GROQ_MODEL", "qwen/qwen3.8-27b")
        if candidate_model.startswith("gemini"):
            candidate_model = "qwen/qwen3.8-27b"

        client = Groq(api_key=api_key)

        groq_messages = []
        if system_prompt:
            groq_messages.append({"role": "system", "content": system_prompt})
        for msg in messages:
            role = "assistant" if msg["role"] == "model" else msg["role"]
            groq_messages.append({"role": role, "content": msg["content"]})

        for attempt in range(2):
            try:
                chat_completion = client.chat.completions.create(
                    messages=groq_messages,
                    model=candidate_model,
                    temperature=0.4,
                    max_tokens=1500,
                )
                raw_content = (
                    chat_completion.choices[0].message.content
                    if chat_completion.choices else None
                )
                logger.info(
                    f"Groq raw response length: {len(raw_content) if raw_content else 0}, "
                    f"model: {candidate_model}"
                )
                if raw_content:
                    cleaned = cls.clean_latex_formatting(raw_content)
                    if not cleaned or not cleaned.strip():
                        cleaned = re.sub(
                            r"<think>.*?</think>", "", raw_content, flags=re.DOTALL
                        ).strip()
                    if cleaned:
                        return cleaned
                logger.warning(f"Groq returned empty content for model {candidate_model}")
                return None

            except APIError as e:
                logger.warning(f"Groq APIError (attempt {attempt + 1}): {e}")
                if "429" in str(e):
                    time.sleep(3.0)
                    continue
                else:
                    break
            except Exception as e:
                logger.warning(
                    f"Groq request failed (attempt {attempt + 1}): {type(e).__name__}: {e}"
                )
                break

        return None

    # ─────────────────────────── text cleaning ─────────────────────────────

    @staticmethod
    def clean_latex_formatting(text: str) -> str:
        """
        Strips raw LaTeX tags, math delimiters, environments, and symbols.
        """
        if not text:
            return text

        text = text.replace('\u2011', '-').replace('\u2013', '-').replace('\u2014', '--')
        text = text.replace('\u202f', ' ').replace('\xa0', ' ')
        text = text.replace('\u2018', "'").replace('\u2019', "'")
        text = text.replace('\u201c', '"').replace('\u201d', '"')

        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.strip().startswith('|') and line.strip().endswith('|'):
                line = re.sub(r'</?(?:ul|ol)[^>]*>', '', line, flags=re.IGNORECASE)
                line = re.sub(r'<li>\s*', '<br>• ', line, flags=re.IGNORECASE)
                line = re.sub(r'</li>', '', line, flags=re.IGNORECASE)
                line = re.sub(r'\|\s*<br>•\s*', '| • ', line)
            else:
                line = re.sub(r'<br\s*/?>', '\n', line, flags=re.IGNORECASE)
                line = re.sub(r'</?(?:ul|ol)[^>]*>', '', line, flags=re.IGNORECASE)
                line = re.sub(r'<li>\s*', '\n• ', line, flags=re.IGNORECASE)
                line = re.sub(r'</li>', '', line, flags=re.IGNORECASE)
                line = re.sub(r'</?p[^>]*>', '\n', line, flags=re.IGNORECASE)
            cleaned_lines.append(line)
        text = '\n'.join(cleaned_lines)

        text = re.sub(r'\\begin\{[a-zA-Z*]+\}', '', text)
        text = re.sub(r'\\end\{[a-zA-Z*]+\}', '', text)
        text = re.sub(r'\\\[\s*(.*?)\s*\\\]', r'\1', text, flags=re.DOTALL)
        text = re.sub(r'\$\$\s*(.*?)\s*\$\$', r'\1', text, flags=re.DOTALL)
        text = re.sub(r'\\\(\s*(.*?)\s*\\\)', r'\1', text)
        text = re.sub(r'\\(?:left|right)\s*([()[\]{}|<>])', r'\1', text)
        text = re.sub(r'\\(?:left|right)\.?', '', text)

        for _ in range(3):
            text = re.sub(r'\\(?:d|t)?frac\{([^{}]+)\}\{([^{}]+)\}', r'\1 / \2', text)

        text = re.sub(r'\\sqrt\{([^{}]+)\}', r'√(\1)', text)
        text = re.sub(r'\^\{?\\circ\}?', '°', text)
        text = re.sub(r'\^\{?2\}?', '²', text)
        text = re.sub(r'\^\{?3\}?', '³', text)

        replacements = [
            (r'\\approx\b', '≈'), (r'\\times\b', '×'), (r'\\div\b', '÷'), (r'\\cdot\b', '·'),
            (r'\\le\b', '≤'), (r'\\ge\b', '≥'), (r'\\ne\b', '≠'), (r'\\to\b', '→'),
            (r'\\infty\b', '∞'), (r'\\\\', '\n'),
        ]
        for pattern, repl in replacements:
            text = re.sub(pattern, repl, text)

        text = re.sub(r'\\text\{([^{}]+)\}', r'\1', text)
        text = re.sub(r'\\mathbf\{([^{}]+)\}', r'**\1**', text)
        text = re.sub(r'\$([^$\n]+)\$', r'\1', text)

        text = re.sub(r'\n\s*[-*•]\s*$', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

