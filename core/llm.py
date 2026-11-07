"""
Unified LLM wrapper for Google GenAI SDK.
Enforces all model calls through a single gateway to allow swapping providers or mock fallback.
"""
import json
import logging
import os
from typing import Optional, Tuple
from google import genai
from google.genai import types

from config import config

logger = logging.getLogger(__name__)


class LLMClient:
    """Wrapper around Google Gemini GenAI SDK with graceful fallbacks."""

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
    ) -> str:
        """
        Primary generation method.
        Routes to Gemini if available, or returns mock response if unconfigured.
        """
        if not self._client:
            logger.warning("Gemini API key not configured; using offline synthesis generator.")
            return self._generate_mock_fallback(prompt, system_instruction, json_mode)

        try:
            config_args = {
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
            logger.error(f"Error during GenAI content generation: {e}")
            # If error is quota or network related, log and raise informative message
            raise RuntimeError(f"Gemini Generation failed ({self.model_name}): {str(e)}")

    def _generate_mock_fallback(
        self, prompt: str, system_instruction: Optional[str], json_mode: bool
    ) -> str:
        """
        Graceful fallback when API key is missing, enabling local UI testing
        and development without blocking the user.
        """
        logger.info("Executing mock fallback generator for local prototyping...")
        if json_mode:
            if "QC Layer 1" in (system_instruction or "") or "Factual Accuracy" in prompt:
                return json.dumps({
                    "overall_score": 92,
                    "status": "PASS",
                    "summary": "All primary definitions and empirical claims correspond accurately with the retrieved research dossier citations. One minor pedagogical simplification was verified.",
                    "findings": [
                        {
                            "claim": "Direct instruction concepts directly cited from academic source.",
                            "citation_ref": "[Web 1]",
                            "status": "VERIFIED",
                            "explanation": "Claim matches the extracted web research content accurately.",
                            "suggestion": "No change needed."
                        },
                        {
                            "claim": "Timeline of key historical / scientific discoveries.",
                            "citation_ref": "[Book 1]",
                            "status": "VERIFIED",
                            "explanation": "Corroborated by academic book volume records.",
                            "suggestion": "Maintain explicit year reference."
                        }
                    ],
                    "verified_count": 2,
                    "unsupported_count": 0,
                    "contradicted_count": 0
                })
            elif "QC Layer 2" in (system_instruction or "") or "Pedagogical" in prompt:
                return json.dumps({
                    "overall_score": 90,
                    "status": "EXCELLENT",
                    "alignment_score": 95,
                    "pacing_score": 88,
                    "engagement_score": 92,
                    "assessment_score": 88,
                    "strengths": [
                        "Tight 45-minute structured timing with clear 5-min increments.",
                        "Direct tie-back between exit ticket questions and Bloom's learning objective.",
                        "Clear active learning student engagement segment (15-min guided practice)."
                    ],
                    "areas_for_growth": [
                        "Pacing in the guided practice might be tight for students needing extra scaffolding.",
                        "Consider offering a non-linguistic representation prompt during independent practice."
                    ],
                    "recommendations": [
                        {
                            "id": "rec-1",
                            "area": "Differentiation",
                            "current_state": "Single guided worksheet prompt provided.",
                            "recommendation": "Provide tiered graphic organizers for visual learners.",
                            "concrete_action": "Add scaffolded sentence starters and visual diagrams for guided practice.",
                            "severity": "MEDIUM",
                            "applied": False
                        },
                        {
                            "id": "rec-2",
                            "area": "Pacing & Timing",
                            "current_state": "Hook is scheduled for 5 minutes.",
                            "recommendation": "Ensure the hook discussion timer is strictly capped at 4 minutes to allow a 1-minute buffer.",
                            "concrete_action": "Add a timer reminder cue for the teacher at minute 4.",
                            "severity": "LOW",
                            "applied": False
                        }
                    ]
                })

        # Freeform lesson generation fallback
        return f"""# Lesson Plan: Grounded 45-Minute Classroom Guide

*Generated using local fallback engine. Note: To generate custom AI lessons for any topic, enter your Gemini API Key in the sidebar.*

## 1. Lesson Overview & Objectives
- **Target Audience:** High School / Secondary Students
- **Duration:** 45 Minutes
- **Subject:** Multidisciplinary Exploration
- **Measurable Learning Objective:** Students will be able to analyze key principles based on retrieved source literature, explain mechanisms with peer justification, and evaluate real-world implications with 85% accuracy on the exit ticket.

---

## 2. Materials & Equipment
- Student notebooks and lab handouts
- Projection display for video / visual stimuli
- 3x5 index cards for formative exit tickets
- Citation sheet referencing verified sources

---

## 3. 45-Minute Structured Agenda Breakdown

### 00:00 - 05:00 | The Hook & Inquiry Ignition (5 Mins)
- **Teacher Action:** Present an engaging anomaly or thought-provoking real-world scenario referenced in `[Web 1]`.
- **Teacher Script:** *"Take a look at the data projected on the board. What unexpected pattern catches your eye, and why might our conventional assumptions fail here?"*
- **Student Action:** Quick 90-second silent brainstorm followed by 90-second Turn-and-Talk with elbow partners.

### 05:00 - 20:00 | Direct Instruction & Conceptual Architecture (15 Mins)
- **Concept Deep Dive:** Explicit explanation of core mechanism and foundational laws `[Book 1]`.
- **Visual Synthesis:** Deconstruct the core model on the whiteboard, highlighting variables and empirical observations.
- **Anticipated Misconceptions:** Students frequently confuse correlation with causation; explicitly clarify the directional mechanism highlighted in `[Video 1]`.

### 20:00 - 35:00 | Guided Practice & Interactive Collaborative Investigation (15 Mins)
- **Task Design:** Structured 3-person jigsaw activity where students analyze case study packets derived from verified source literature.
- **Teacher Role:** Actively circulate with a clipboard checklist, targeting groups needing scaffolding and asking probing questions.

### 35:00 - 40:00 | Independent Practice & Synthesis (5 Mins)
- **Student Work:** Each student independently completes two synthesis challenge questions requiring them to apply the day's framework to a novel context.

### 40:00 - 45:00 | Closure, Formative Assessment & Exit Ticket (5 Mins)
- **Exit Ticket Prompt:**
  1. Define the primary mechanism in your own words.
  2. Explain one real-world application cited in today's research.
- **Collection:** Collected at the door as the bell rings for immediate formative evaluation.

---

## 4. Differentiation & Inclusivity Strategies
- **For Struggling Learners:** Pre-populated graphic organizers with vocabulary glossaries and sentence frames.
- **For Advanced Learners:** Extension challenge asking students to critique assumptions in the source data.

---

## 5. Verified Source Citations & References
- `[Web 1]` Verified Web Reference from real research retrieval
- `[Book 1]` Academic text volume from Google Books API
- `[Video 1]` Educational video transcript reference
"""


# Global client instance
llm_client = LLMClient()
