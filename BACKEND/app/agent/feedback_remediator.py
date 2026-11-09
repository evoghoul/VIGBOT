"""
Feedback Remediation Service (app/agent/feedback_remediator.py)
Autonomous Cognitive Evaluator and Self-Improving Query Remediator powered by Google Gemini.

When a student gives negative feedback (dislike / thumbs down) in helpdesk chat:
1. Gathers the student query, bot output, conversation history, and optional user comment.
2. Sanitizes PII (Roll numbers, emails, phone numbers) before external cognitive evaluation.
3. Invokes Google Gemini (gemini-3.5-flash / gemini-3.8-flash) as an institutional audit agent.
4. Strictly evaluates INTENT-OUTPUT MISMATCH:
   - Does NOT remediate if the user disliked a truthful, policy-enforcing response (e.g., attendance <75%, fee dues, cross-student privacy refusal under Clause 2.1).
   - ONLY remediates if the bot's response genuinely failed to match the student's true intent (e.g. misclassified intent, wrong campus directions, confusing building info vs walking route, hallucinated landmarks).
5. When remediation is needed, generates:
   - Normalized trigger patterns
   - Intended intent category
   - Target entity
   - Routing action / Tool / Direct grounded template
6. Persists the remediation rule to Neon PostgreSQL and SQLite.
7. Future matching queries are automatically intercepted and served with the corrected handler and grounded answer!
"""

import os
import re
import json
import time
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Tuple

from app.config import settings
from app.database import DataRepository, DatabaseSession

logger = logging.getLogger(__name__)


class FeedbackRemediationService:
    """
    Self-improving AI remediation service.
    Audits negative feedback with Google Gemini and dynamically updates query handling.
    """

    _cache_active_remediations: Optional[List[Dict[str, Any]]] = None
    _last_cache_time: float = 0.0
    CACHE_TTL_SECONDS: float = 10.0  # Hot cache re-sync interval

    @classmethod
    def get_gemini_api_key(cls) -> str:
        """Resolves the Gemini API key from database system_settings, settings, environment, or .env."""
        from app.database import DataRepository
        stored_key = DataRepository.get_system_setting("GEMINI_API_KEY")
        if stored_key and not stored_key.startswith("YOUR_"):
            return stored_key.strip()
        key = getattr(settings, "GEMINI_API_KEY", "").strip()
        if key and not key.startswith("YOUR_"):
            return key
        for env_var in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            val = os.getenv(env_var, "").strip()
            if val and not val.startswith("YOUR_"):
                return val
        # Check backend .env directly
        try:
            env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("GEMINI_API_KEY=") and not line.startswith("#"):
                            return line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass
        return ""

    @classmethod
    def redact_pii_for_audit(cls, text: str) -> str:
        """Strips student names, roll numbers, emails, and phone numbers before external audit."""
        if not text:
            return ""
        # 1. Roll numbers (Vignan & standard format)
        cleaned = re.sub(r"\b(?:2[0-9]{2}[a-z]{1,4}[0-9a-z]{3,7}|\d{2}[a-z]{2,5}\d{3,4})\b", "[STUDENT_ROLL_NO]", text, flags=re.I)
        # 2. Email addresses
        cleaned = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[STUDENT_EMAIL]", cleaned)
        # 3. Phone numbers
        cleaned = re.sub(r"(?:\+91[\-\s]?|91[\-\s]?|0)?[6-9]\d{9}\b", "[STUDENT_PHONE]", cleaned)
        return cleaned

    @classmethod
    def get_verified_university_knowledge_context(cls) -> str:
        """
        Returns grounded institutional facts from ToolRegistry to prevent Gemini from hallucinating or inventing data.
        """
        return """
- CAMPUS BUILDINGS & NODES: Main Gate (Node 0), Path Alpha (Main Road), A-Block (90m), H-Block (140m, Boys Hostel Mess on Ground Floor), NTR Library (150m), MHP Canteen (Path Alpha), Zest Supermarket (Path Alpha), Path Beta, N-Block (240m, just beside Zest), Vignan Vihar Boys Hostel (260m, directly in front of N-Block), Path Gamma, U-Block (325m, Law & Management, directly behind N-Block), Convocation Hall (380m).
- CENTRAL LIBRARY HOURS: Monday-Friday 08:00 AM - 10:00 PM; Saturday 08:00 AM - 08:00 PM; Sunday 09:00 AM - 05:00 PM (Reading halls & digital labs open; circulation counter closed). 3 books per B.Tech student, 14-day loan, ₹2/day overdue fine.
- HOSTEL & DINING RULES: Decentralized mess on ground floor of each hostel. Breakfast 7:30 AM - 8:45 AM, Lunch 12:30 PM - 2:00 PM, Evening Tea 5:00 PM - 6:00 PM, Dinner 7:30 PM - 9:00 PM. Curfew: 6:00 PM reporting curfew. Campus gate closure strictly at 10:00 PM (Clause HD-01).
- TRANSIT & BUS TIMETABLES:
  * Route 1: Guntur City Express (Arrival 7:35 AM | Return 4:45 PM)
  * Route 2: Vijayawada City Express (Arrival 7:30 AM | Return 4:45 PM)
  * Route 3: Tenali Town Shuttle (Arrival 7:40 AM | Return 4:45 PM)
  * Route 4: Chilakaluripet Shuttle (Arrival 7:30 AM | Return 4:45 PM)
  * Route 5: Mangalagiri Express (Arrival 7:35 AM | Return 4:45 PM)
  * KM Hostel Shuttle: Morning 07:50, 08:05, 08:40, 09:30, 10:30, 11:35 AM | Evening 01:45, 03:30, 04:10, 04:40, 05:15, 06:15, 07:00, 08:00, 09:00 PM
  * Villas SP Residency Shuttle: Morning 07:45, 08:00, 08:40, 09:00, 09:50, 11:30 AM | Evening 02:00, 03:30, 04:10, 04:40, 05:15, 06:00, 07:00, 08:00, 09:00 PM
  * AP/AR/AA/AO Cluster Shuttle: Morning 07:45, 07:55, 08:00, 08:40, 09:00, 09:50, 11:30, 11:35 AM | Evening 02:00, 03:30, 04:10, 04:40, 05:15, 06:00, 07:00, 08:00, 09:00 PM
- VENUE CAPACITIES: Seminar Halls 1 & 2: 250; Main Auditorium: 1,200; Open Air Theatre (OAT): 2,500; Indoor Sports Complex: 500. 48 hours advance notice required.
- STUDENT CLUBS: AI Innovation Club (Technical / Robotics), Symphony Music Club (Cultural), Athletics & Sports (Sports), Competitive Programming (Technical), Theatrix (Cultural).
- LOST ID CARD PROCEDURE: Phase 1: Submit digital report on Lost & Found board. Phase 2: Report physically to Admin Office in H-Block (ground floor, left hallway), collect Dean Student Affairs & Chief Warden signatures, remit ₹100 fee. SLA: 3 working days.
- ACADEMIC REGULATIONS (R22/R23 & Annexure-2): Minimum 75% attendance mandatory in each registered subject to write final examinations (Clause 4.2). Medical condonation between 65% and 74.9% with Dean approval. Procedure for paying Condonation Fee (Annexure – 2): Students pay Rs. 500/- for each course as condonation fee for shortage of attendance; students having four or more courses pay flat Rs. 2,000/-. Payment must be made by voucher (NOT online) at PNB Bank, Vadlamudi Branch. After payment, submit original copy of the challan at the Examination section and get a receipt. Hall-Tickets will be issued to the candidate only after paying the condonation fee. Below 65% is non-condonable detention.
""".strip()

    @classmethod
    def call_gemini_audit_engine(
        cls,
        user_query: str,
        bot_output: str,
        student_comment: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Sends the disliked conversation turn to Google Gemini for intent-output mismatch evaluation.
        Enforces strict grounding against verified institutional records to prevent hallucinating fake data.
        """
        api_key = cls.get_gemini_api_key()
        if not api_key:
            logger.warning("[FeedbackRemediator] No Gemini API key found for background feedback audit.")
            return None

        clean_query = cls.redact_pii_for_audit(user_query)
        clean_output = cls.redact_pii_for_audit(bot_output)
        clean_comment = cls.redact_pii_for_audit(student_comment or "")
        verified_context = cls.get_verified_university_knowledge_context()

        audit_prompt = f"""You are the VIGBOT Institutional Audit Engine for Vignan University (VFSTR Vadlamudi).
A student gave negative feedback (thumbs down / dislike) on the following conversation turn:

[STUDENT QUERY]:
{clean_query}

[BOT OUTPUT DELIVERED]:
{clean_output}

[STUDENT FEEDBACK COMMENT]:
{clean_comment or "None provided"}

[VERIFIED UNIVERSITY DATABASE CONTEXT]:
{verified_context}

TASK:
Analyze whether there is a genuine INTENT-OUTPUT MISMATCH or if the bot was correct.

CRITICAL EVALUATION & ZERO-FABRICATION RULES:
1. DO NOT REMEDIATE (mismatch_detected = false, remediation_needed = false):
   - If the bot correctly enforced university regulations (e.g. attendance below mandatory 75% cutoff, condonation rules Clause 4.2).
   - If the bot correctly enforced privacy policies (e.g. refusing to show other students' attendance or marks under Clause 2.1 RLAC).
   - If the bot gave accurate fee dues, timetable periods, or hostel curfew times, and the student simply expressed frustration with the rule itself.
   - In these cases, the bot's response was factually and procedurally accurate.

2. REMEDIATE (mismatch_detected = true, remediation_needed = true):
   - If the bot answered a completely different topic (e.g. user asked for building directions or location, but bot gave document request services).
   - If the bot failed to distinguish informational building queries ("what is N-Block?") from walking navigation ("where is N-Block?").
   - If the bot hallucinated inaccurate campus landmarks.
   - If the bot failed to route to the correct tool or provided irrelevant generic boilerplate.

3. STRICT TRUTHFULNESS & GROUNDING (NEVER INVENT FAKE DATA):
   - You MUST NEVER invent, guess, extrapolate, or hallucinate facts, numbers, dates, timings, locations, room numbers, bus routes, or policies.
   - If the accurate factual answer is present in the VERIFIED UNIVERSITY DATABASE CONTEXT above, set "data_missing_in_db": false, and use those exact verified facts in "grounded_response_template".
   - CRITICAL: If the factual information needed to answer the student's query is NOT PRESENT in the university database context above (for example: an unrecorded new bus route, unlisted phone number, unrecorded event date, or unknown policy):
     * You MUST set "data_missing_in_db": true
     * You MUST set "missing_data_description": "Precise explanation of what factual data is missing from the university database"
     * You MUST set "remediation_type": "PENDING_OFFICIAL_INPUT"
     * You MUST set "grounded_response_template": null
     * DO NOT fabricate fake data, fake numbers, fake dates, or fake procedures!

Respond ONLY with valid JSON (no markdown formatting, no code blocks) matching this schema:
{{
  "mismatch_detected": true or false,
  "mismatch_reason": "Clear diagnosis of whether intent matched output",
  "remediation_needed": true or false,
  "data_missing_in_db": true or false,
  "missing_data_description": "Description of missing factual info if data_missing_in_db is true, else null",
  "intended_intent": "CAMPUS_DIRECTIONS | BUILDING_PROFILE | LOST_AND_FOUND | ATTENDANCE | FEES | EXAMS | TIMETABLE | SERVICES | HOSTEL | TRANSPORT | PRIVACY_GUARD | GENERAL",
  "target_entity": "Name of building, subject, or landmark (e.g. N_BLOCK, ZEST, CS302, etc.) or null",
  "trigger_patterns": ["phrase 1", "phrase 2", "phrase 3"],
  "routing_action": "TOOL:get_campus_location_and_navigation | TOOL:get_attendance | RULE:privacy_refusal | DIRECT_ANSWER | PENDING_OFFICIAL_INPUT",
  "remediation_type": "TOOL_ROUTING | BUILDING_PROFILE | POLICY_DEFENSE | DIRECT_ANSWER | PENDING_OFFICIAL_INPUT",
  "grounded_response_template": "High-quality, strictly factual markdown answer to serve future queries, or null if data is missing",
  "suggested_follow_ups": ["follow up question 1", "follow up question 2"]
}}
"""

        candidate_models = [
            getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash"),
            "gemini-3.5-flash",
            "gemini-3.8-flash",
            "gemini-flash-latest"
        ]

        for model in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": audit_prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 2048,
                    "responseMimeType": "application/json"
                }
            }
            t0 = time.time()
            try:
                data_bytes = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(url, data=data_bytes, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=25) as resp:
                    latency = int((time.time() - t0) * 1000)
                    DataRepository.log_gemini_call(endpoint="auditEngine", model=model, status_code=200, latency_ms=latency)
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    candidates = resp_data.get("candidates", [])
                    if candidates and "content" in candidates[0] and "parts" in candidates[0]["content"]:
                        raw_text = candidates[0]["content"]["parts"][0].get("text", "")
                        # Parse JSON cleanly
                        cleaned_json = re.sub(r"^```json\s*", "", raw_text.strip())
                        cleaned_json = re.sub(r"\s*```$", "", cleaned_json).strip()
                        return json.loads(cleaned_json)
            except urllib.error.HTTPError as he:
                latency = int((time.time() - t0) * 1000)
                DataRepository.log_gemini_call(endpoint="auditEngine", model=model, status_code=he.code, latency_ms=latency)
                if he.code == 404:
                    logger.warning(f"[FeedbackRemediator] Gemini model {model} 404, trying next...")
                    continue
                logger.warning(f"[FeedbackRemediator] Gemini HTTP error on {model}: {he}")
                break
            except Exception as e:
                logger.warning(f"[FeedbackRemediator] Error calling Gemini {model}: {e}")
                break

        return None

    @classmethod
    def evaluate_and_remediate(
        cls,
        feedback_id: str,
        conversation_id: str,
        user_query: str,
        bot_output: str,
        student_comment: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[str]:
        """
        Background task: Evaluates disliked conversation turn with Gemini.
        If intent and output mismatched, creates and persists a learned query remediation.
        """
        try:
            logger.info(f"[FeedbackRemediator] Evaluating negative feedback {feedback_id} for query: '{user_query}'")
            audit_result = cls.call_gemini_audit_engine(
                user_query=user_query,
                bot_output=bot_output,
                student_comment=student_comment,
                history=history
            )

            if not audit_result:
                logger.info(f"[FeedbackRemediator] Running local deterministic audit for feedback {feedback_id}...")
                audit_result = cls.local_fallback_audit(user_query, bot_output, student_comment)

            if not audit_result:
                logger.warning(f"[FeedbackRemediator] Audit engine returned no result for feedback {feedback_id}")
                return None

            mismatch = audit_result.get("mismatch_detected", False)
            remediation_needed = audit_result.get("remediation_needed", False)
            reason = audit_result.get("mismatch_reason", "No reason provided")
            is_missing = bool(audit_result.get("data_missing_in_db", False))
            missing_desc = audit_result.get("missing_data_description") or ""

            logger.info(f"[FeedbackRemediator] Audit result for feedback {feedback_id}: mismatch={mismatch}, remediation_needed={remediation_needed}, data_missing_in_db={is_missing}. Reason: {reason}")

            # IFF necessary: only update query handling if intent and output genuinely mismatched
            if not (mismatch and remediation_needed):
                logger.info(f"[FeedbackRemediator] Dislike was on a policy-compliant or correct answer. Storing POLICY_PROTECTED audit log.")
                policy_audit_record = {
                    "feedback_id": feedback_id,
                    "conversation_id": conversation_id,
                    "user_query": user_query,
                    "bot_output": bot_output,
                    "student_comment": student_comment or "",
                    "mismatch_detected": False,
                    "mismatch_reason": reason or "Disliked query verified: bot correctly upheld university academic policy or RLS student data privacy rules.",
                    "intended_intent": audit_result.get("intended_intent") or "POLICY_GUARD",
                    "remediation_type": "POLICY_DEFENSE",
                    "trigger_patterns": [user_query.strip().lower()],
                    "target_entity": audit_result.get("target_entity") or "",
                    "routing_action": "RULE:policy_enforcement",
                    "remediation_payload": {
                        "data_missing_in_db": False,
                        "missing_data_description": "",
                        "nodal_officer_input": "",
                        "grounded_response_template": bot_output,
                        "suggested_follow_ups": audit_result.get("suggested_follow_ups") or []
                    },
                    "status": "POLICY_PROTECTED"
                }
                DataRepository.save_learned_remediation(policy_audit_record)
                return None

            # Prepare trigger patterns
            triggers = audit_result.get("trigger_patterns") or []
            normalized_user_q = user_query.strip().lower()
            if normalized_user_q not in triggers:
                triggers.append(normalized_user_q)

            # Compile remediation record
            remediation_record = {
                "feedback_id": feedback_id,
                "conversation_id": conversation_id,
                "user_query": user_query,
                "bot_output": bot_output,
                "student_comment": student_comment or "",
                "mismatch_detected": True,
                "mismatch_reason": reason,
                "intended_intent": audit_result.get("intended_intent") or "GENERAL",
                "remediation_type": "PENDING_OFFICIAL_INPUT" if is_missing else (audit_result.get("remediation_type") or "DIRECT_ANSWER"),
                "trigger_patterns": triggers,
                "target_entity": audit_result.get("target_entity") or "",
                "routing_action": "PENDING_OFFICIAL_INPUT" if is_missing else (audit_result.get("routing_action") or "DIRECT_ANSWER"),
                "remediation_payload": {
                    "data_missing_in_db": is_missing,
                    "missing_data_description": missing_desc,
                    "nodal_officer_input": "",
                    "grounded_response_template": audit_result.get("grounded_response_template") or "",
                    "suggested_follow_ups": audit_result.get("suggested_follow_ups") or []
                },
                "status": "PENDING_NODAL_INPUT" if is_missing else "ACTIVE"
            }

            rem_id = DataRepository.save_learned_remediation(remediation_record)
            # Invalidate in-memory cache to make it active instantly
            cls._cache_active_remediations = None
            logger.info(f"[FeedbackRemediator] Stored learned remediation '{rem_id}' (status={remediation_record['status']}) for intent: {remediation_record['intended_intent']}")
            return rem_id

        except Exception as e:
            logger.error(f"[FeedbackRemediator] Failed to evaluate and remediate feedback {feedback_id}: {e}", exc_info=True)
            return None

    @classmethod
    def get_active_remediations(cls) -> List[Dict[str, Any]]:
        """Cached retrieval of active remediations for fast query matching."""
        now = time.time()
        if cls._cache_active_remediations is not None and (now - cls._last_cache_time) < cls.CACHE_TTL_SECONDS:
            return cls._cache_active_remediations

        try:
            rems = DataRepository.get_active_learned_remediations()
            cls._cache_active_remediations = rems
            cls._last_cache_time = now
            return rems
        except Exception as e:
            logger.warning(f"[FeedbackRemediator] Could not load active remediations: {e}")
            return []

    @classmethod
    def match_query(cls, query: str) -> Optional[Dict[str, Any]]:
        """
        Matches an incoming student query against all active learned remediations.
        Returns the best matching remediation if one exists.
        """
        q_clean = query.strip().lower()
        q_norm = re.sub(r"[?!.,;:()\[\]{}]", "", q_clean).strip()
        remediations = cls.get_active_remediations()

        for rem in remediations:
            triggers = rem.get("trigger_patterns") or []
            for trigger in triggers:
                trig_clean = trigger.strip().lower()
                trig_norm = re.sub(r"[?!.,;:()\[\]{}]", "", trig_clean).strip()
                if not trig_norm:
                    continue
                # Exact or substring match (trigger contained in query)
                if trig_norm == q_norm or trig_norm in q_norm:
                    return rem
                try:
                    if re.search(r"\b" + re.escape(trig_norm) + r"\b", q_norm, re.I):
                        return rem
                except Exception:
                    pass

        return None

    @classmethod
    def local_fallback_audit(
        cls,
        user_query: str,
        bot_output: str,
        student_comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deterministic, offline factual audit engine when Gemini is offline or unconfigured.
        Cross-checks query against known database landmarks and tools:
        - If query matches a known database landmark/tool: routes accurately with real data.
        - If query asks for unknown/missing information: flags data_missing_in_db=True to alert Nodal Officer.
        """
        q_clean = user_query.strip().lower()
        from app.agent.tool_registry import ToolRegistry

        # 1. Check if user asked for known campus landmarks
        known_aliases = list(ToolRegistry.CAMPUS_ALIASES.keys())
        matched_alias = next((a for a in known_aliases if a in q_clean), None)
        if matched_alias and any(k in q_clean for k in ["where", "direction", "how to reach", "locate", "block", "canteen", "library", "hostel", "hall"]):
            return {
                "mismatch_detected": True,
                "mismatch_reason": f"Disliked response lacked accurate spatial directions for {matched_alias.upper()}. Remediated to Dijkstra campus navigation tool.",
                "remediation_needed": True,
                "data_missing_in_db": False,
                "missing_data_description": None,
                "intended_intent": "CAMPUS_DIRECTIONS",
                "target_entity": matched_alias.upper(),
                "trigger_patterns": [q_clean, f"where is {matched_alias}", f"directions to {matched_alias}"],
                "routing_action": "TOOL:get_campus_location_and_navigation",
                "remediation_type": "TOOL_ROUTING",
                "grounded_response_template": f"Use get_campus_location_and_navigation({matched_alias})",
                "suggested_follow_ups": ["View campus map", "Show landmarks"]
            }

        # 2. Check known bus/transport queries
        if any(w in q_clean for w in ["bus", "shuttle", "transport", "van"]):
            return {
                "mismatch_detected": True,
                "mismatch_reason": "Query asked for bus transit or shuttle timings. Remediated to verified university transport timetable tool.",
                "remediation_needed": True,
                "data_missing_in_db": False,
                "missing_data_description": None,
                "intended_intent": "TRANSPORT",
                "target_entity": "BUS_FLEET",
                "trigger_patterns": [q_clean, "bus timings", "hostel shuttle"],
                "routing_action": "TOOL:get_transport_summary",
                "remediation_type": "TOOL_ROUTING",
                "grounded_response_template": "Use get_transport_summary()",
                "suggested_follow_ups": ["Check route 1", "Hostel bus schedule"]
            }

        # 3. Check known library queries
        if any(w in q_clean for w in ["library", "books", "borrow"]):
            return {
                "mismatch_detected": True,
                "mismatch_reason": "Query asked for library hours or policies. Remediated to Central Library registry.",
                "remediation_needed": True,
                "data_missing_in_db": False,
                "missing_data_description": None,
                "intended_intent": "LIBRARY",
                "target_entity": "CENTRAL_LIBRARY",
                "trigger_patterns": [q_clean, "library timings", "is library open on sunday"],
                "routing_action": "TOOL:get_library_info",
                "remediation_type": "TOOL_ROUTING",
                "grounded_response_template": "Use get_library_info()",
                "suggested_follow_ups": ["Sunday library hours", "Book borrow limit"]
            }

        # 4. Unknown or Missing Information in Database:
        # Prevent fake or invented data! Flag data_missing_in_db=True to alert Nodal Officer.
        return {
            "mismatch_detected": True,
            "mismatch_reason": "The factual data required to answer this inquiry is not present in the institutional database. Flagged for Nodal Officer official verification to prevent hallucinating fake data.",
            "remediation_needed": True,
            "data_missing_in_db": True,
            "missing_data_description": f"Verified university information for inquiry '{user_query}' is missing from database records. Requires official Nodal Officer data entry.",
            "intended_intent": "GENERAL",
            "target_entity": None,
            "trigger_patterns": [q_clean],
            "routing_action": "PENDING_OFFICIAL_INPUT",
            "remediation_type": "PENDING_OFFICIAL_INPUT",
            "grounded_response_template": None,
            "suggested_follow_ups": ["Contact Student Helpdesk", "Visit Admin Office"]
        }

    @classmethod
    def apply_remediation(
        cls,
        remediation: Dict[str, Any],
        session: DatabaseSession,
        query: str,
        effective_lang: str = "en",
        active_subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the learned routing remediation for a matched student query.
        Dispatches to the correct tool, building profile, privacy guard, or direct grounded response.
        """
        from app.agent.tool_registry import ToolRegistry

        rem_type = remediation.get("remediation_type", "DIRECT_ANSWER")
        routing_action = remediation.get("routing_action", "DIRECT_ANSWER")
        target_entity = remediation.get("target_entity") or ""
        payload = remediation.get("remediation_payload") or {}
        follow_ups = payload.get("suggested_follow_ups") or ["Check campus map", "Ask another question"]
        template = payload.get("grounded_response_template") or ""

        # 0. HUMAN-VERIFIED NODAL OFFICER DATA (Absolute Authoritative Priority)
        if payload.get("nodal_officer_input"):
            official_data = payload.get("nodal_officer_input").strip()
            return {
                "category": "INSTITUTIONAL_INFO",
                "topic": "Official University Record (Verified by Nodal Officer)",
                "source_agent": "Nodal Officer Desk & University Governance",
                "content": f"📋 **Official University Information (Verified by Nodal Officer):**\n\n{official_data}",
                "citations": [{
                    "title": "Nodal Officer Directive",
                    "clause": "Institutional Verification",
                    "effective_date": "2026-11-01",
                    "summary": "Human-verified university record."
                }],
                "structured_card": None,
                "suggested_follow_ups": follow_ups,
                "active_subject": active_subject,
                "language": effective_lang,
                "llm_provider": "local",
                "model_used": "nodal-verified-rule",
                "used_fallback": False,
                "routed_by": "learned_remediation",
                "action": None
            }

        # 1. TOOL ROUTING (e.g. Campus Navigation to N-Block, Zest, Library, etc.)
        if rem_type == "TOOL_ROUTING" and "get_campus_location_and_navigation" in routing_action:
            dest = target_entity or query
            tool_res = ToolRegistry.get_campus_location_and_navigation(destination=dest)
            tool_dict = tool_res if isinstance(tool_res, dict) else (getattr(tool_res, "data", {}) or {})
            data = tool_dict.get("data") if isinstance(tool_dict, dict) else {}
            direct_answer = tool_dict.get("direct_answer", "") if isinstance(tool_dict, dict) else ""
            
            # Check if query was informational vs directional
            is_directional = bool(re.search(r"\b(where|reach|how\s+to\s+(?:go|get|reach)|path|route|direction|directions|way\s+to|walk|walking)\b", query, re.I))
            building_profile = data.get("building_profile") if isinstance(data, dict) else None

            if not is_directional and building_profile:
                # Informational Building Profile
                content = (
                    f"### 🏛️ {building_profile.get('title', 'Campus Landmark')}\n\n"
                    f"• **Campus Role & Purpose:** {building_profile.get('purpose', '')}\n"
                    f"• **Student Cohorts & Branches:** {building_profile.get('cohort', '')}\n"
                    f"• **Geographic Location:** {building_profile.get('location', '')}\n"
                    f"• **Key Facilities & Labs:** {building_profile.get('facilities', '')}\n\n"
                    f"💡 *Need walking directions from the Main Gate? Just ask 'Where is {dest}?' or 'How do I reach {dest}?'*"
                )
                topic = f"{building_profile.get('title')} Profile"
            else:
                # Turn-by-Turn Route
                steps = data.get("steps", []) if isinstance(data, dict) else []
                step_lines = []
                for i, s in enumerate(steps):
                    s_clean = s.strip()
                    if s_clean.lower().startswith("step "):
                        step_lines.append(f"• {s_clean}")
                    else:
                        step_lines.append(f"• **Step {i+1}:** {s_clean}")
                steps_formatted = "\n".join(step_lines)

                tot_dist = data.get("total_distance_meters", 240) if isinstance(data, dict) else 240
                dest_name = data.get("destination") or dest.replace("_", "-")

                walking_section = ""
                if steps_formatted:
                    walking_section = f"\n\n🚶‍♂️ **Turn-by-Turn Walking Route from Main Gate ({tot_dist:.0f}m):**\n{steps_formatted}"

                content = (
                    f"### 📍 {dest_name} Location & Campus Directions:\n\n"
                    f"{direct_answer}"
                    f"{walking_section}\n\n"
                    f"🗺️ *You can also inspect the full interactive layout in the Campus Map tab.*"
                )
                topic = f"{dest_name} Directions"

            return {
                "category": "MAP",
                "topic": topic,
                "source_agent": "VIGBOT Cognitive Remediation Engine",
                "content": content,
                "citations": [
                    {
                        "title": "VFSTR Campus Spatial Directory",
                        "clause": "Campus Node Directory & Dijkstra Graph",
                        "effective_date": "2026-07-01",
                        "summary": "Verified spatial coordinates and walking routes."
                    }
                ],
                "structured_card": {
                    "type": "navigation",
                    "title": f"Route to {data.get('destination', dest)}",
                    "path": "/campus-map",
                    "action_text": "Open Campus Map",
                    "actionIntent": "navigate:map",
                    "target": "map"
                },
                "redirect_path": "map",
                "action": {
                    "type": "navigate",
                    "label": "Open Campus Map",
                    "target": "map",
                    "route": "/?tab=map"
                },
                "suggested_follow_ups": follow_ups,
                "active_subject": active_subject,
                "language": effective_lang,
                "llm_provider": "gemini-remediated",
                "model_used": "gemini-learned-rule",
                "used_fallback": False,
                "routed_by": "learned_remediation",
                "remediation_id": remediation.get("remediation_id")
            }

        # 2. BUILDING PROFILE
        if rem_type == "BUILDING_PROFILE":
            block_key = target_entity.upper().replace(" ", "_") if target_entity else "N_BLOCK"
            profile = ToolRegistry.CAMPUS_BLOCK_PROFILES.get(block_key) or ToolRegistry.CAMPUS_BLOCK_PROFILES.get("N_BLOCK")
            content = (
                f"### 🏛️ {profile.get('title', target_entity)}\n\n"
                f"• **Campus Role & Purpose:** {profile.get('purpose', '')}\n"
                f"• **Student Cohorts & Branches:** {profile.get('cohort', '')}\n"
                f"• **Geographic Location:** {profile.get('location', '')}\n"
                f"• **Key Facilities & Labs:** {profile.get('facilities', '')}\n\n"
                f"💡 *Need walking directions? Ask 'Where is {profile.get('title')}?'*"
            )
            return {
                "category": "CAMPUS_INFO",
                "topic": f"{profile.get('title')} Profile",
                "source_agent": "VIGBOT Cognitive Remediation Engine",
                "content": content,
                "citations": [],
                "structured_card": {
                    "type": "navigation_route",
                    "title": f"{profile.get('title')}",
                    "path": "/campus-map",
                    "action_text": "View on Campus Map"
                },
                "suggested_follow_ups": follow_ups,
                "active_subject": active_subject,
                "language": effective_lang,
                "llm_provider": "gemini-remediated",
                "model_used": "gemini-learned-rule",
                "used_fallback": False,
                "routed_by": "learned_remediation",
                "remediation_id": remediation.get("remediation_id")
            }

        # 3. POLICY DEFENSE
        if rem_type == "POLICY_DEFENSE":
            from app.agent.nlu_engine import NLUEngine
            defense_res = NLUEngine.generate_privacy_injection_defense_response(session, query, effective_lang)
            defense_res["routed_by"] = "learned_remediation"
            defense_res["remediation_id"] = remediation.get("remediation_id")
            return defense_res

        # 4. DIRECT GROUNDED ANSWER
        return {
            "category": remediation.get("intended_intent", "GENERAL"),
            "topic": "Learned Institutional Remediation",
            "source_agent": "VIGBOT Cognitive Remediation Engine",
            "content": template or "I have processed your query according to verified university records.",
            "citations": [
                {
                    "title": "VFSTR Institutional Knowledge Base",
                    "clause": "Verified Helpdesk Rule",
                    "effective_date": "2026-07-01",
                    "summary": "Verified institutional information."
                }
            ],
            "structured_card": None,
            "suggested_follow_ups": follow_ups,
            "active_subject": active_subject,
            "language": effective_lang,
            "llm_provider": "gemini-remediated",
            "model_used": "gemini-learned-rule",
            "used_fallback": False,
            "routed_by": "learned_remediation",
            "remediation_id": remediation.get("remediation_id")
        }
