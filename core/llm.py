"""
Unified LLM wrapper for Google GenAI SDK.
Includes exponential backoff, JSON auto-repair/retries, failure simulation hooks for demos,
and offline fallback synthesis.
"""
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from google import genai
from google.genai import types

from config import config

logger = logging.getLogger(__name__)


# Global simulation failure state (developer mode)
SIMULATED_FAILURE: Optional[str] = None


def set_simulated_failure(failure_type: Optional[str]):
    """Sets a simulated failure mode for demo recording."""
    global SIMULATED_FAILURE
    SIMULATED_FAILURE = failure_type


def get_simulated_failure() -> Optional[str]:
    return SIMULATED_FAILURE


class LLMClient:
    """Wrapper around Google Gemini GenAI SDK with resilience and retry logic."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or config.gemini_api_key
        self.model_name = model or config.gemini_model or "gemini-2.5-flash"
        self._client: Optional[genai.Client] = None
        self._init_client()

    def _init_client(self):
        """Initializes the google-genai client if API key is present."""
        if self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize GenAI client: {e}")
                self._client = None
        else:
            self._client = None

    def update_key_and_model(self, api_key: str, model: Optional[str] = None):
        """Update active API key and model dynamically at runtime."""
        self.api_key = api_key
        if model:
            self.model_name = model
        self._init_client()

    def is_configured(self) -> bool:
        """Returns True if a valid client is configured."""
        return self._client is not None

    def test_connection(self) -> Tuple[bool, str]:
        """Test API connectivity with a minimal ping."""
        if not self._client:
            return False, "No Gemini API key configured. Please set GEMINI_API_KEY."
        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents="Hello, confirm you are online with 'OK'.",
                config=types.GenerateContentConfig(
                    max_output_tokens=10,
                    temperature=0.1
                )
            )
            return True, f"Connected to {self.model_name}: {response.text.strip()}"
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            return False, f"API Error: {str(e)}"

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        json_mode: bool = False,
        call_purpose: str = "general",
    ) -> str:
        """
        Primary generation method with exponential backoff and demo failure simulation.
        """
        # Check demo failure simulation hooks
        if SIMULATED_FAILURE:
            if SIMULATED_FAILURE == "generation" and call_purpose in ["generation", "lesson"]:
                raise RuntimeError("Simulated AI Generation Failure: Service temporarily unavailable (Demo Mode).")
            elif SIMULATED_FAILURE == "qc1" and call_purpose in ["qc1", "factual"]:
                raise RuntimeError("Simulated QC Layer 1 Failure: Fact-checking reviewer timed out (Demo Mode).")
            elif SIMULATED_FAILURE == "qc2" and call_purpose in ["qc2", "pedagogy"]:
                raise RuntimeError("Simulated QC Layer 2 Failure: Pedagogical reviewer engine unreachable (Demo Mode).")
            elif SIMULATED_FAILURE == "malformed_json" and json_mode:
                return "{'invalid_json': true, unquoted_key: 123,,}"

        if not self._client:
            logger.warning("Gemini API key not configured; using offline synthesis generator.")
            return self._generate_mock_fallback(prompt, system_instruction, json_mode, call_purpose)

        # Exponential backoff retry loop (up to 3 attempts)
        max_retries = 3
        delay = 2.0
        last_error = None

        for attempt in range(max_retries):
            try:
                config_args: Dict[str, Any] = {
                    "temperature": temperature,
                }
                if system_instruction:
                    config_args["system_instruction"] = system_instruction
                if json_mode:
                    config_args["response_mime_type"] = "application/json"

                gen_config = types.GenerateContentConfig(**config_args)

                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=gen_config,
                )

                if not response.text:
                    raise ValueError("Empty response received from Gemini model.")
                return response.text

            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                # If rate-limited or transient network error, back off
                if "429" in err_str or "quota" in err_str or "timeout" in err_str or "resourceexhausted" in err_str:
                    logger.warning(f"Gemini call attempt {attempt+1} failed with transient error: {e}. Backing off {delay}s...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    # Non-retriable error
                    logger.error(f"Error during GenAI content generation: {e}")
                    raise RuntimeError(f"Gemini Generation failed ({self.model_name}): {str(e)}")

        raise RuntimeError(f"Gemini Generation failed after {max_retries} attempts: {str(last_error)}")

    def generate_json_with_repair(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        call_purpose: str = "json",
    ) -> Dict[str, Any]:
        """
        Generates structured JSON with up to 2 auto-repair attempts if malformed.
        """
        raw_text = self.generate_text(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            json_mode=True,
            call_purpose=call_purpose,
        )

        # Attempt 1: Parse initial response
        initial_error = "Unknown parse failure"
        try:
            return self._parse_json(raw_text)
        except Exception as e1:
            initial_error = str(e1)
            logger.warning(f"Initial JSON parse failed: {e1}. Initiating Auto-Repair Attempt 1...")

        # Repair Attempt 1: Ask model to fix syntax
        repair_prompt = f"""The following JSON response is malformed. Fix the syntax errors and return ONLY clean, valid JSON matching the original schema.

MALFORMED TEXT:
{raw_text}
"""
        try:
            repaired_text = self.generate_text(
                prompt=repair_prompt,
                system_instruction="You are a JSON repair tool. Return only valid JSON.",
                temperature=0.0,
                json_mode=True,
                call_purpose=call_purpose,
            )
            return self._parse_json(repaired_text)
        except Exception as e2:
            logger.warning(f"Auto-Repair Attempt 1 failed: {e2}. Initiating Auto-Repair Attempt 2...")

        # Repair Attempt 2: Final cleanup with regex extraction
        cleaned = re.sub(r"[\n\r\t]", " ", raw_text)
        match = re.search(r"(\{.*\})", cleaned)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass

        raise ValueError(f"Failed to produce valid JSON after auto-repair attempts. Initial error: {initial_error}")

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Robust parser that cleans markdown fences and extracts JSON dict."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[len("```json"):].strip()
        elif text.startswith("```"):
            text = text[len("```"):].strip()
        if text.endswith("```"):
            text = text[:-3].strip()

        # Find outer braces
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            text = match.group(1)

        return json.loads(text)

    def _generate_mock_fallback(
        self, prompt: str, system_instruction: Optional[str], json_mode: bool, call_purpose: str
    ) -> str:
        """
        Deterministic, high-quality mock responses for local testing when no key is set.
        """
        logger.info(f"Executing mock fallback generator for call_purpose: '{call_purpose}'")

        if "relevance" in call_purpose or "relevance_note" in prompt.lower():
            return json.dumps({
                "relevance_notes": [
                    "Provides foundational definitions and protocol specifications directly addressing the learning objective.",
                    "Explains architectural trade-offs and concrete practical examples referenced in the guided activity.",
                    "Offers clear visual analogies and common misconception checks cited in direct instruction."
                ]
            })

        if "qc1" in call_purpose or "QC Layer 1" in (system_instruction or ""):
            return json.dumps({
                "verdict": "Needs revision",
                "confidence_note": "Audited with high rigor against all 6 retrieved sources. Verified protocol methods and status categories; flagged 1 ungrounded assertion.",
                "what_was_verified": "Verified GET and POST method idempotence and safety rules against [S1]. Verified 2xx, 4xx, and 5xx status category definitions against [S2].",
                "issues": [
                    {
                        "id": "qc1-1",
                        "severity": "medium",
                        "location": "Key methods/techniques with examples",
                        "issue_found": "The explanation claims that POST requests are inherently encrypted, which confuses HTTP transport encryption (HTTPS/TLS) with the POST method specification.",
                        "evidence": "RFC 9110 and MDN [S1] state: 'POST request bodies are sent in plain text unless encrypted by TLS (HTTPS)'.",
                        "suggested_improvement": "Clarify that POST places data inside the message body rather than the URL query string, but requires HTTPS for cryptographic security.",
                        "applied": False,
                        "source_layer": "qc1"
                    },
                    {
                        "id": "qc1-2",
                        "severity": "low",
                        "location": "Categories/second concept",
                        "issue_found": "Status code 500 is described simply as 'server broken', which is overly vague for college/advanced prep.",
                        "evidence": "[S2] states: '500 Internal Server Error is a generic catch-all indicating the server encountered an unexpected condition that prevented it from fulfilling the request'.",
                        "suggested_improvement": "Explicitly identify 500 as 'Internal Server Error' (generic unhandled exception) vs 503 (Service Unavailable).",
                        "applied": False,
                        "source_layer": "qc1"
                    }
                ]
            })

        if "qc2" in call_purpose or "QC Layer 2" in (system_instruction or ""):
            return json.dumps({
                "verdict": "Needs revision",
                "confidence_note": "Evaluated against 45-minute bell-to-bell instructional design. Objective coverage is strong; pacing in the practical activity is slightly ambitious.",
                "what_was_verified": "Checked Bloom's taxonomy alignment for GET/POST differentiation and status code classification. All 3 objective parts are explicitly taught and tested.",
                "objective_coverage": [
                    {
                        "objective_part": "Explain GET and POST methods and their functional differences",
                        "where_taught": "Core concept explanation & Key methods (10 mins)",
                        "where_tested": "Questions and recap (Questions 1, 2, 4)",
                        "covered": True
                    },
                    {
                        "objective_part": "Distinguish between 2xx (Success), 4xx (Client Error), and 5xx (Server Error)",
                        "where_taught": "Categories/second concept (8 mins)",
                        "where_tested": "Practical activity & Questions 3, 5",
                        "covered": True
                    },
                    {
                        "objective_part": "Practical diagnostic troubleshooting using status codes",
                        "where_taught": "Practical activity (7 mins)",
                        "where_tested": "Questions 6, 7 (Application scenarios)",
                        "covered": True
                    }
                ],
                "issues": [
                    {
                        "id": "qc2-1",
                        "severity": "medium",
                        "location": "Practical activity",
                        "issue_found": "The activity asks students to inspect 6 distinct network requests in 7 minutes, which leaves under 70 seconds per case for paired discussion.",
                        "evidence": "Recommended active learning pacing is 2-3 minutes per diagnostic scenario for introductory learners.",
                        "suggested_improvement": "Reduce the guided activity from 6 scenarios to 3 focused cases (one 200, one 404, one 500), and move the remaining three to extension practice.",
                        "applied": False,
                        "source_layer": "qc2"
                    },
                    {
                        "id": "qc2-2",
                        "severity": "low",
                        "location": "Introduction",
                        "issue_found": "The term 'payload' is introduced in the first 2 minutes before being conceptually defined.",
                        "evidence": "Pedagogical best practice: Define technical jargon upon first exposure.",
                        "suggested_improvement": "Add a simple 1-sentence lay definition: 'payload (the data package being carried)' when first mentioned.",
                        "applied": False,
                        "source_layer": "qc2"
                    }
                ]
            })

        # Structured Lesson Generator Fallback (JSON)
        if json_mode and ("sections" in prompt or "lesson" in call_purpose or "generation" in call_purpose or "lesson plan" in prompt.lower()):
            return json.dumps({
                "title": "HTTP Requests and Responses: Methods and Status Codes",
                "objective": "Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories.",
                "total_minutes": 45,
                "sections": [
                    {
                        "title": "Introduction: The Hidden Conversation Behind Every Click",
                        "minutes": 3,
                        "content": "Imagine ordering a meal at a restaurant: you make a specific request from the menu, and the kitchen returns your plate—or an explanation if an ingredient ran out. Every web interaction operates on this exact client-server contract [S1]. In this 45-minute lesson, we will uncover how computers exchange information using HTTP GET and POST methods, and decode the universal status codes that tell us whether our requests succeeded or failed [S2].",
                        "word_count": 75,
                        "timing_feasibility": "Good",
                        "words_per_minute": 130.0
                    },
                    {
                        "title": "Core Concept: The Architecture of HTTP Messages",
                        "minutes": 7,
                        "content": "The Hypertext Transfer Protocol (HTTP) is an application-layer request-response protocol powering the World Wide Web [S1]. Every HTTP transaction consists of two messages: the Request sent by the client (browser, mobile app, or script) and the Response returned by the server [S3]. An HTTP Request contains a method line (specifying action and path), headers (metadata such as `Content-Type` and `Authorization`), and an optional body payload [S1]. The server processes this request and returns a Response containing a status line (e.g. `HTTP/1.1 200 OK`), response headers, and the response body (HTML, JSON, or media) [S2].",
                        "word_count": 115,
                        "timing_feasibility": "Good",
                        "words_per_minute": 130.0
                    },
                    {
                        "title": "Key Methods: Differentiating GET vs. POST",
                        "minutes": 10,
                        "content": "Two primary methods dominate web communication: GET and POST [S1].\n\n1. **GET (Safe & Idempotent):** Used strictly to retrieve data without altering server state. Parameters are appended directly to the URL query string (e.g. `/search?q=photosynthesis`). GET requests can be bookmarked, cached by CDNs, and re-executed safely without duplicate charges [S1].\n\n```http\nGET /api/v1/students?grade=10 HTTP/1.1\nHost: school.edu\nAccept: application/json\n```\n\n2. **POST (State-Changing & Non-Idempotent):** Used to submit data for the server to process, store, or modify (e.g. submitting a form, creating a database record, or uploading a file) [S1]. Data is transmitted inside the HTTP message body, not the URL.\n\n```http\nPOST /api/v1/enroll HTTP/1.1\nHost: school.edu\nContent-Type: application/json\n\n{\n  \"student_id\": \"S1042\",\n  \"course\": \"Biology\"\n}\n```",
                        "word_count": 160,
                        "timing_feasibility": "Good",
                        "words_per_minute": 130.0
                    },
                    {
                        "title": "Response Status Categories: 2xx, 4xx, and 5xx",
                        "minutes": 8,
                        "content": "Every HTTP response begins with a three-digit status code organized into standardized categories [S2]:\n\n- **2xx (Success):** The client's request was successfully received, understood, and accepted. The most common is `200 OK` (standard success) and `201 Created` (new resource created after a POST) [S2].\n- **4xx (Client Error):** The request contains syntax errors or cannot be fulfilled due to client mistake. Key examples include `400 Bad Request` (malformed JSON), `401 Unauthorized` (missing credentials), `403 Forbidden` (authenticated but denied permission), and `404 Not Found` (resource does not exist) [S2].\n- **5xx (Server Error):** The server failed to fulfill an apparently valid request due to an internal crash or upstream failure. Key examples include `500 Internal Server Error` (unhandled server exception) and `503 Service Unavailable` (server overloaded or in maintenance) [S2].",
                        "word_count": 145,
                        "timing_feasibility": "Good",
                        "words_per_minute": 130.0
                    },
                    {
                        "title": "Selected Video Segment: Visualizing the Wire",
                        "minutes": 5,
                        "content": "We will now observe a 3-minute visual segment from *HTTP Protocol Breakdown* [S3]. Suggested playback: 01:15 to 04:15. Notice how the browser's developer tools network tab displays the request headers, the status code pill, and the response payload in real time. (Note: Transcript excerpt verified in research dossier) [S3].",
                        "word_count": 55,
                        "timing_feasibility": "Good",
                        "words_per_minute": 130.0
                    },
                    {
                        "title": "Practical Activity: The HTTP Diagnostic Lab",
                        "minutes": 7,
                        "content": "**Step-by-Step Student Instructions:**\nWorking with your elbow partner, analyze the 3 HTTP diagnostic logs below. For each log, determine: (a) Was the request a GET or POST? (b) Which status code category was returned? (c) Whose responsibility is the failure (Client or Server)?\n\n- **Case A:** `POST /api/login HTTP/1.1` -> Response: `401 Unauthorized`\n- **Case B:** `GET /dashboard/grades HTTP/1.1` -> Response: `200 OK`\n- **Case C:** `POST /checkout/pay HTTP/1.1` -> Response: `500 Internal Server Error`\n\n**Worked Solution for Teacher:**\n- Case A: POST method; 4xx Client Error (user provided invalid password; client must correct credentials) [S2].\n- Case B: GET method; 2xx Success (data retrieved successfully) [S2].\n- Case C: POST method; 5xx Server Error (database connection dropped during transaction; server infrastructure bug) [S2].",
                        "word_count": 140,
                        "timing_feasibility": "Good",
                        "words_per_minute": 130.0
                    },
                    {
                        "title": "Comprehension Questions and Recap",
                        "minutes": 5,
                        "content": "**Recap:** HTTP operates on stateless client requests and server responses [S1]. GET retrieves data safely; POST transmits state-changing data [S1]. Status 2xx signals success, 4xx signals client errors, and 5xx signals server infrastructure faults [S2].\n\n**Comprehension Questions (With Solutions):**\n1. *Recall:* What is the primary difference in how GET and POST pass parameters? (Answer: GET passes data via URL query strings; POST passes data within the message body payload) [S1].\n2. *Classification:* A user enters an incorrect password into an online portal. Which status category should the server return? (Answer: 4xx Client Error, specifically 401 Unauthorized) [S2].\n3. *Analysis:* Why is it unsafe to use GET for a fund transfer link like `/transfer?amount=500`? (Answer: GET is meant to be idempotent and safe; pre-fetching bots or browser refreshes would trigger repeated unintended transfers) [S1].\n4. *Application:* A web API crashes because a database runs out of disk space. Does the client receive a 4xx or 5xx code? (Answer: 5xx Server Error, as the fault lies entirely with server infrastructure) [S2].\n5. *Synthesis:* If a server successfully creates a new account record following a POST request, what specific 2xx code is most accurate? (Answer: `201 Created`) [S2].",
                        "word_count": 210,
                        "timing_feasibility": "Good",
                        "words_per_minute": 130.0
                    }
                ],
                "relevant_videos": [
                    {
                        "title": "HTTP Protocol Crash Course",
                        "url": "https://www.youtube.com/watch?v=iYM2zFP3Zn0",
                        "channel": "Traversy Media",
                        "note": "Optional supplemental walkthrough of browser developer tools."
                    }
                ],
                "cited_source_ids": ["S1", "S2", "S3"]
            })

        return "Standard offline text response."


# Global client instance
llm_client = LLMClient()
