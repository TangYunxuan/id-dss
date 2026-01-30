"""
LLM Service - AI/LLM integration for instructional design support.

Supports both OpenAI and Anthropic providers.
"""
from typing import Dict, Any, Optional, List
import json

from app.config import settings, LLMProvider

# Lazy imports to avoid errors if packages not installed
_openai_client = None
_anthropic_client = None


def _get_openai_client():
    """Get or create OpenAI client."""
    global _openai_client
    if _openai_client is None:
        try:
            from openai import OpenAI
            _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        except ImportError as e:
            raise ImportError(
                f"openai package not installed (or failed to import). "
                f"Run: pip install openai. Original error: {e}"
            ) from e
    return _openai_client


def _get_anthropic_client():
    """Get or create Anthropic client."""
    global _anthropic_client
    if _anthropic_client is None:
        try:
            import anthropic
            _anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        except ImportError as e:
            raise ImportError(
                f"anthropic package not installed (or failed to import). "
                f"Run: pip install anthropic. Original error: {e}"
            ) from e
    return _anthropic_client


async def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Call the configured LLM provider.
    
    Args:
        system_prompt: System message for context
        user_prompt: User message/query
    
    Returns:
        LLM response text
    """
    if settings.LLM_PROVIDER == LLMProvider.OPENAI:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        
        client = _get_openai_client()
        try:
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            # Best-effort mapping to actionable error messages.
            status_code = getattr(e, "status_code", None) or getattr(e, "status", None)
            message = str(e)
            message_lower = message.lower()

            # Quota / billing errors often surface as 429 with 'insufficient_quota'
            if status_code == 429 and ("insufficient_quota" in message_lower or "quota" in message_lower):
                raise ValueError(
                    "OpenAI quota exceeded / billing not enabled for this API key. "
                    "Check your OpenAI plan & billing, or switch to another provider."
                ) from e

            # Rate limit (also 429) but not quota-related
            if status_code == 429:
                raise ValueError(
                    "OpenAI rate limit exceeded. Please retry later or reduce request frequency."
                ) from e

            if status_code in (401, 403) or "invalid api key" in message_lower or "authentication" in message_lower:
                raise ValueError(
                    "OpenAI authentication failed. Verify OPENAI_API_KEY and the associated project/org access."
                ) from e

            raise ValueError(f"OpenAI request failed: {message}") from e
    
    elif settings.LLM_PROVIDER == LLMProvider.ANTHROPIC:
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        
        client = _get_anthropic_client()
        try:
            response = client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return response.content[0].text
        except Exception as e:
            status_code = getattr(e, "status_code", None) or getattr(e, "status", None)
            message = str(e)
            if status_code == 429:
                raise ValueError(
                    "Anthropic rate limit exceeded. Please retry later or reduce request frequency."
                ) from e
            if status_code in (401, 403):
                raise ValueError(
                    "Anthropic authentication failed. Verify ANTHROPIC_API_KEY and account access."
                ) from e
            raise ValueError(f"Anthropic request failed: {message}") from e

    elif settings.LLM_PROVIDER == LLMProvider.GEMINI:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not configured")

        try:
            import google.generativeai as genai
            from google.generativeai.types import GenerationConfig
        except ImportError as e:
            raise ImportError(
                f"google-generativeai package not installed (or failed to import). "
                f"Run: pip install google-generativeai. Original error: {e}"
            ) from e

        genai.configure(api_key=settings.GEMINI_API_KEY)

        # In google-generativeai, system_instruction is supported on the model.
        model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            system_instruction=system_prompt,
        )
        response = model.generate_content(
            user_prompt,
            generation_config=GenerationConfig(temperature=0.7),
        )

        # Prefer the library's .text helper, fall back safely.
        text = getattr(response, "text", None)
        if text:
            return text
        return str(response)
    
    else:
        raise ValueError(f"Unknown LLM provider: {settings.LLM_PROVIDER}")


# ============================================================
# PROMPTS
# ============================================================

OBJECTIVE_ANALYSIS_SYSTEM_PROMPT = """You are an expert instructional designer with deep knowledge of:
- Bloom's Taxonomy (cognitive, affective, psychomotor domains)
- Backward Design principles
- ADDIE model
- Constructive alignment

Your task is to analyze learning objectives and provide actionable feedback.

Always respond in valid JSON format with this structure:
{
    "overall_assessment": "Brief overall evaluation",
    "bloom_analysis": [
        {
            "objective": "The objective text",
            "current_level": "Knowledge/Comprehension/Application/Analysis/Synthesis/Evaluation",
            "domain": "Cognitive/Affective/Psychomotor",
            "is_measurable": true/false,
            "suggestion": "How to improve this objective"
        }
    ],
    "alignment_notes": "Notes on how objectives align with each other",
    "missing_coverage": ["Areas that might need additional objectives"],
    "improved_objectives": ["Rewritten objectives with improvements"]
}"""

OBJECTIVE_ANALYSIS_USER_PROMPT = """Please analyze the following learning objectives for the course:

**Course Title:** {course_title}
**Education Level:** {level}
**Delivery Modality:** {modality}
**Constraints:** {constraints}

**Learning Objectives:**
{objectives}

Provide a detailed analysis with suggestions for improvement."""


ACTIVITY_SUGGESTION_SYSTEM_PROMPT = """You are an expert instructional designer specializing in learning activity design.

Your expertise includes:
- Active learning strategies
- Collaborative learning techniques
- Assessment-integrated activities
- Technology-enhanced learning
- Differentiated instruction

Generate learning activities that:
1. Directly support the learning objectives
2. Are appropriate for the education level and modality
3. Include varied activity types (individual, group, hands-on, reflective)
4. Consider time and resource constraints

Always respond in valid JSON format with this structure:
{
    "activities": [
        {
            "title": "Activity name",
            "type": "Discussion/Project/Lab/Assessment/Reflection/Presentation/Simulation/Case Study",
            "description": "Detailed description of the activity",
            "objective_alignment": ["Which objectives this addresses"],
            "duration": "Estimated time",
            "materials_needed": ["Required materials or tools"],
            "instructions": ["Step-by-step instructions"],
            "assessment_criteria": "How to assess student performance",
            "adaptations": {
                "online": "How to adapt for online delivery",
                "accessibility": "Accessibility considerations"
            }
        }
    ],
    "sequence_rationale": "Why this sequence of activities works well",
    "total_estimated_time": "Total time for all activities"
}"""

ACTIVITY_SUGGESTION_USER_PROMPT = """Generate learning activities for the following course:

**Course Title:** {course_title}
**Education Level:** {level}
**Delivery Modality:** {modality}
**Constraints:** {constraints}

**Learning Objectives:**
{objectives}

Please suggest 3-5 diverse learning activities that effectively support these objectives."""


ASSESSMENT_RECOMMENDATION_SYSTEM_PROMPT = """You are an expert in educational assessment design.

Your expertise includes:
- Formative and summative assessment strategies
- Rubric development
- Authentic assessment design
- Assessment validity and reliability

Generate assessment recommendations that:
1. Align directly with learning objectives
2. Include both formative and summative options
3. Are appropriate for the modality and level
4. Provide clear criteria for success

Always respond in valid JSON format with this structure:
{
    "assessments": [
        {
            "title": "Assessment name",
            "type": "Formative/Summative",
            "method": "Quiz/Project/Presentation/Portfolio/Peer Review/Self-Assessment/Exam/Paper",
            "description": "Detailed description",
            "objective_alignment": ["Which objectives this assesses"],
            "timing": "When in the course this should occur",
            "weight": "Suggested percentage of final grade (if summative)",
            "rubric_criteria": ["Key criteria for evaluation"],
            "feedback_strategy": "How feedback will be provided"
        }
    ],
    "assessment_strategy_rationale": "Overall rationale for this assessment approach",
    "formative_summative_balance": "Explanation of balance between assessment types"
}"""

ASSESSMENT_RECOMMENDATION_USER_PROMPT = """Recommend assessments for the following course:

**Course Title:** {course_title}
**Education Level:** {level}
**Delivery Modality:** {modality}
**Constraints:** {constraints}

**Learning Objectives:**
{objectives}

**Planned Activities:**
{activities}

Please recommend appropriate assessments that align with the objectives and activities."""


# ============================================================
# API FUNCTIONS
# ============================================================

async def generate_objective_analysis(
    course_title: str,
    level: str,
    modality: str,
    objectives: str,
    constraints: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze learning objectives and provide improvement suggestions.
    """
    user_prompt = OBJECTIVE_ANALYSIS_USER_PROMPT.format(
        course_title=course_title,
        level=level,
        modality=modality,
        constraints=constraints or "None specified",
        objectives=objectives,
    )
    
    response_text = await _call_llm(OBJECTIVE_ANALYSIS_SYSTEM_PROMPT, user_prompt)
    return _parse_json_response(response_text)


async def generate_activity_suggestions(
    course_title: str,
    level: str,
    modality: str,
    objectives: str,
    constraints: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate learning activity suggestions based on objectives.
    """
    user_prompt = ACTIVITY_SUGGESTION_USER_PROMPT.format(
        course_title=course_title,
        level=level,
        modality=modality,
        constraints=constraints or "None specified",
        objectives=objectives,
    )
    
    response_text = await _call_llm(ACTIVITY_SUGGESTION_SYSTEM_PROMPT, user_prompt)
    return _parse_json_response(response_text)


async def generate_assessment_recommendations(
    course_title: str,
    level: str,
    modality: str,
    objectives: str,
    activities: str,
    constraints: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate assessment recommendations aligned with objectives and activities.
    """
    user_prompt = ASSESSMENT_RECOMMENDATION_USER_PROMPT.format(
        course_title=course_title,
        level=level,
        modality=modality,
        constraints=constraints or "None specified",
        objectives=objectives,
        activities=activities,
    )
    
    response_text = await _call_llm(ASSESSMENT_RECOMMENDATION_SYSTEM_PROMPT, user_prompt)
    return _parse_json_response(response_text)


def _parse_json_response(response_text: str) -> Dict[str, Any]:
    """
    Parse LLM response, extracting JSON if wrapped in markdown code blocks.
    """
    text = response_text.strip()
    
    # Remove markdown code blocks if present
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    
    if text.endswith("```"):
        text = text[:-3]
    
    text = text.strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Return as raw text if JSON parsing fails
        return {"raw_response": response_text, "parse_error": True}
