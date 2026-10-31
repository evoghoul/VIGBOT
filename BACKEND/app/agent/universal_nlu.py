"""
VIGBOT Universal Semantic NLU & Action Intelligence Engine.
Provides:
1. Discourse-aware multi-turn context resolution (anaphora 'open it', topic switching, missing params).
2. Distinction between Asking (Information), Navigating (Navigation), Doing (Action), Tracking (Status), and Canceling.
3. Multilingual and colloquial understanding (Hinglish, slang, typos, abbreviations).
4. Strict False-Action Prevention Guard across all 28 application capabilities.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from app.agent.capability_registry import (
    APPLICATION_CAPABILITIES,
    CommunicationIntent,
    OperationType,
    find_matching_capability
)


class UniversalNLU:
    """
    Universal semantic understanding layer for VIGBOT.
    Handles multi-turn discourse, multilingual idioms, and guarantees zero unauthorized actions.
    """

    # Hinglish & colloquial mappings
    HINGLISH_TRANSLATIONS = {
        "kahan": "where",
        "kidhar": "where",
        "kaise": "how",
        "karo": "do",
        "kholo": "open",
        "dikhao": "show",
        "batao": "tell",
        "bata": "tell",
        "chahiye": "need",
        "karna hai": "want to do",
        "daalna hai": "want to submit",
        "lagana hai": "want to apply",
        "kya scene hai": "what is status",
        "kahan milega": "where to find",
        "pata karna hai": "want to know",
        "meri": "my",
        "mera": "my",
        "apna": "my",
        "isko": "it",
        "use": "it",
        "ise": "it",
        "usko": "that",
        "ye": "this",
        "yeh": "this",
        "wo": "that",
        "woh": "that"
    }

    @classmethod
    def normalize_query_semantics(cls, query: str) -> str:
        """
        Normalizes slang, Hinglish, punctuation, and typographical variations
        into standardized semantic tokens while preserving the raw query.
        """
        q = query.lower().strip()
        # Clean punctuation except hyphens/quotes
        q = re.sub(r"[?!.,;:()\[\]{}]", " ", q)
        words = q.split()
        normalized_words = [cls.HINGLISH_TRANSLATIONS.get(w, w) for w in words]
        normalized_q = " ".join(normalized_words)
        return normalized_q

    @classmethod
    def resolve_contextual_capability(
        cls,
        query: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Resolves the target capability from the current query or multi-turn history
        (e.g., resolving 'open it', 'take me there', 'yes please').
        """
        # 1. Direct query matching
        direct_match = find_matching_capability(query)
        if direct_match is not None:
            return direct_match

        # 2. Anaphoric reference resolution from recent conversation history
        q_norm = cls.normalize_query_semantics(query)
        anaphora_triggers = [
            "open it", "take me there", "go there", "show it", "navigate there",
            "open that", "open the tab", "kholo", "yes", "yes please", "sure",
            "open page", "take me", "view it", "show that", "let's go",
            "open this", "show this", "kholo isko", "isko kholo", "open", "kholo"
        ]
        has_anaphora = any(trig in q_norm or q_norm == trig for trig in anaphora_triggers)

        if has_anaphora and conversation_history:
            # Search backwards through recent assistant turns for capability mentions
            for msg in reversed(conversation_history):
                content = msg.get("content", "").lower()
                meta = msg.get("responseMeta") or {}
                redirect_path = meta.get("redirect_path") or msg.get("redirect_path")
                
                # Check explicit redirect_path in metadata
                if redirect_path and redirect_path in APPLICATION_CAPABILITIES:
                    return APPLICATION_CAPABILITIES[redirect_path]

                # Check category or capability name in message
                for cap_id, cap in APPLICATION_CAPABILITIES.items():
                    if cap["name"].lower() in content or cap_id in content or cap["category"].lower() in content:
                        return cap

        return None

    @classmethod
    def parse_communication_intent(
        cls,
        query: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> CommunicationIntent:
        """
        Determines the student's communication intent using deep semantic parsing.
        Distinguishes:
        - INFORMATION_REQUEST (asking where/how/rules)
        - NAVIGATION_REQUEST (asking to open/switch views)
        - ACTION_REQUEST (asking to execute, book, submit, report)
        - CANCEL_REQUEST (asking to cancel/abort/withdraw)
        - STATUS_LOOKUP (checking approval, tracking ticket)
        - PERSONAL_DATA_REQUEST (fetching authenticated student record)
        - GENERAL_ACADEMIC (pedagogical/subject tutoring)
        - AMBIGUOUS (underspecified)
        - CONVERSATION (greetings/social)
        """
        q_raw = query.strip()
        q_norm = cls.normalize_query_semantics(query)
        q_lower = q_raw.lower()

        # 1. Negative request with Information intent ("Don't submit anything, just tell me where...")
        if any(neg in q_norm for neg in ["don't", "dont", "do not"]):
            if any(info_word in q_norm for info_word in ["tell me", "where", "how", "what", "details", "info", "show", "find"]):
                return CommunicationIntent.INFORMATION_REQUEST

        # 2. Negative / Abort / Cancellation Intent
        cancel_markers = [
            "cancel my", "cancel that", "cancel booking", "withdraw application",
            "cancel request", "abort", "don't book", "dont book", "don't submit",
            "dont submit", "stop that", "actually cancel", "forget that"
        ]
        if any(cm in q_norm for cm in cancel_markers):
            return CommunicationIntent.CANCEL_REQUEST

        # 2. Greetings and Pleasantries
        greetings = ["hello", "hi", "hey", "namaste", "good morning", "good evening", "thank you", "thanks", "bye"]
        if q_lower in greetings:
            return CommunicationIntent.CONVERSATION

        # 3. Status Tracking & Lookup Intent
        status_markers = [
            "status of", "track my ticket", "track my request", "track my application",
            "has my application", "has my request", "is my application", "is my request",
            "is my ticket", "is my complaint", "check status", "ticket status",
            "application status", "any update on", "is it approved", "whether it is approved",
            "i already submitted", "what is status", "kahan tak pahuncha", "kya hua",
            "track ticket", "sr-2026-", "anc-"
        ]
        if any(sm in q_norm or sm in q_lower for sm in status_markers):
            return CommunicationIntent.STATUS_LOOKUP

        # 4. Explicit Navigation Request ("Open Lost & Found", "Take me to attendance", "kholo", "open it")
        nav_triggers = [
            "open", "go to", "take me to", "navigate to", "show tab", "switch to",
            "view tab", "take me there", "go there", "open it", "kholo", "show me the tab"
        ]
        if any(q_norm.startswith(nt) or f" {nt} " in f" {q_norm} " for nt in nav_triggers):
            # Check if there's a target capability in query or history
            target_cap = cls.resolve_contextual_capability(query, conversation_history)
            if target_cap is not None:
                return CommunicationIntent.NAVIGATION_REQUEST

        # 5. Negative phrasing with info intent ("Don't book anything, just tell me where it is")
        if "don't" in q_norm or "dont" in q_norm:
            if any(info_word in q_norm for info_word in ["tell me", "where", "how", "what", "details"]):
                return CommunicationIntent.INFORMATION_REQUEST

        # 6. Informational Request (ASKING, NOT DOING!)
        # CRITICAL: Asking where/how to do something is NEVER an action request!
        info_markers = [
            "where can i", "where do i", "where to", "how do i", "how can i", "how to",
            "how am i supposed to", "where do i go for", "where can i find", "tell me where",
            "tell me how", "what is the process", "what is the procedure", "who should i contact",
            "is there a way to", "rules for", "what are the timings", "kahan", "kaise",
            "can i know", "tell me about", "details about", "kahan milega"
        ]
        if any(im in q_norm for im in info_markers):
            return CommunicationIntent.INFORMATION_REQUEST

        # 7. General Academic Concept Inquiries (DSA, DBMS, OS, Mathematics, Electronics)
        academic_concepts = [
            "normalization", "1nf", "2nf", "3nf", "bcnf", "binary search", "quicksort",
            "mergesort", "stack", "queue", "linked list", "flip-flop", "flip flop", "8051",
            "microcontroller", "deadlock", "paging", "osi layer", "tcp", "udp", "dsa",
            "discrete math", "boolean algebra", "bubble sort", "acid properties", "eigenvalues",
            "laplace transform", "fourier transform", "differential equation"
        ]
        if any(term in q_lower for term in academic_concepts) and not any(k in q_lower for k in ["my attendance", "my fee", "my marks"]):
            return CommunicationIntent.GENERAL_ACADEMIC

        # 8. Personal Student Data Inquiries
        personal_markers = [
            "my attendance", "meri attendance", "my fees", "my marks", "my cgpa", "my sgpa",
            "my timetable", "my classes", "classes i attended", "my hostel room", "my advisor",
            "my mentor", "am i eligible", "will i reach 75", "can i sit in exam", "classes needed"
        ]
        if any(pm in q_norm for pm in personal_markers):
            return CommunicationIntent.PERSONAL_DATA_REQUEST

        # 9. Ambiguous Queries (Underspecified)
        # Note: Open help requests ("help me", "start", "menu") trigger the personalized proactive academic briefing
        ambiguous_phrases = [
            "i found something", "found something", "i lost something", "lost something",
            "i have a problem", "i have an issue", "need to report something", "report an issue",
            "help with something", "something went wrong"
        ]
        if q_lower in ambiguous_phrases or any(q_lower == p for p in ambiguous_phrases):
            return CommunicationIntent.AMBIGUOUS

        # 10. Explicit Action Request (DOING: User explicitly asks to book, apply, submit, report)
        action_markers = [
            "i want to report", "i want to submit", "i want to apply", "please report",
            "please submit", "please apply", "book a", "register for", "apply for",
            "lodge grievance", "file complaint", "submit grievance", "claim this item",
            "i need to get this done", "submit this", "do this for me", "i want to book",
            "i want to join", "join the club", "apply for bonafide", "need a bonafide",
            "want a bonafide", "apply karna", "book karna", "submit karna", "daalna hai",
            "lagana hai", "chahiye"
        ]
        if any(am in q_norm for am in action_markers):
            return CommunicationIntent.ACTION_REQUEST

        # Default fallback: If it references an application feature, treat as informational guidance
        matching_cap = cls.resolve_contextual_capability(query, conversation_history)
        if matching_cap is not None:
            return CommunicationIntent.INFORMATION_REQUEST

        return CommunicationIntent.INFORMATION_REQUEST

    @classmethod
    def resolve_and_execute(
        cls,
        session: Any,
        query: str,
        student_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Universal capability-aware resolution engine.
        Enforces false-action guards, handles multi-turn references,
        and returns structured responses with verified navigation payloads.
        """
        comm_intent = cls.parse_communication_intent(query, conversation_history)
        matching_cap = cls.resolve_contextual_capability(query, conversation_history)

        # -------------------------------------------------------------------
        # 1. CANCEL / ABORT REQUEST: Safely acknowledge cancellation without writes
        # -------------------------------------------------------------------
        if comm_intent == CommunicationIntent.CANCEL_REQUEST:
            cap_name = matching_cap["name"] if matching_cap else "operation"
            return {
                "content": f"Understood. I have canceled this {cap_name} request. No changes were made to your records.",
                "category": matching_cap["category"] if matching_cap else "GENERAL",
                "topic": "Request Canceled",
                "source_agent": "VIGBOT (Workflow Controller)",
                "redirect_path": matching_cap["frontend_tab"] if matching_cap else None,
                "action": None,
                "structured_card": None,
                "citations": [],
                "routed_by": "universal_nlu"
            }

        # -------------------------------------------------------------------
        # 2. STATUS LOOKUP: Track actual database tickets, never fabricate!
        # -------------------------------------------------------------------
        if comm_intent == CommunicationIntent.STATUS_LOOKUP:
            q_upper = query.upper()
            # Extract possible tracking number (e.g. SR-2026-0213, ANC-1024)
            sr_match = re.search(r"\b(SR-\d{4}-\d{4,5})\b", q_upper)
            anc_match = re.search(r"\b(ANC-\d{4,5})\b", q_upper)

            # Check Service Request database
            if sr_match and session:
                from app.database import DataRepository
                req_no = sr_match.group(1)
                user_requests = DataRepository.list_service_requests(session)
                found_req = next((r for r in user_requests if r.get("request_no") == req_no), None)
                if found_req:
                    return {
                        "content": (
                            f"📋 **Official Status for Ticket {req_no}:**\n\n"
                            f"• **Category:** {found_req.get('category')}\n"
                            f"• **Title:** {found_req.get('title')}\n"
                            f"• **Assigned Office:** {found_req.get('assigned_office', 'Registrar Office')}\n"
                            f"• **Current Status:** **{found_req.get('status')}**\n"
                            f"• **Estimated SLA Date:** {found_req.get('sla_due_date', 'Within 3 working days')}"
                        ),
                        "category": "SERVICE_REQUEST",
                        "topic": f"Status: {req_no}",
                        "source_agent": "VIGBOT (Ticket Tracker)",
                        "redirect_path": "services",
                        "action": {
                            "type": "navigate",
                            "label": "Open Student Services",
                            "target": "services",
                            "route": "/?tab=services"
                        },
                        "structured_card": None,
                        "citations": [],
                        "routed_by": "universal_nlu"
                    }
                else:
                    return {
                        "content": (
                            f"I searched your student records, but could not find an active ticket matching **{req_no}**.\n"
                            f"Please verify the tracking number or view your submitted requests in the **Student Services** tab."
                        ),
                        "category": "SERVICE_REQUEST",
                        "topic": "Ticket Not Found",
                        "source_agent": "VIGBOT (Ticket Tracker)",
                        "redirect_path": "services",
                        "action": {
                            "type": "navigate",
                            "label": "View All Requests",
                            "target": "services",
                            "route": "/?tab=services"
                        },
                        "structured_card": None,
                        "citations": [],
                        "routed_by": "universal_nlu"
                    }

            # General status lookup for active submissions
            q_lower_clean = query.lower()
            is_explicit_recent_query = any(k in q_lower_clean for k in [
                "recent request", "my latest request", "my recent application",
                "status of my request", "status of my application", "check my request status",
                "application status", "ticket status"
            ])
            if session and is_explicit_recent_query:
                from app.database import DataRepository
                recent_requests = DataRepository.list_service_requests(session)
                if recent_requests:
                    latest = recent_requests[-1]
                    return {
                        "content": (
                            f"Here is the status of your most recent administrative request:\n\n"
                            f"• **Tracking No:** **{latest.get('request_no')}**\n"
                            f"• **Service:** {latest.get('title')}\n"
                            f"• **Current Status:** **{latest.get('status')}**\n"
                            f"• **Office:** {latest.get('assigned_office')}\n\n"
                            f"You can view all your submissions in the Student Services tab."
                        ),
                        "category": "SERVICES",
                        "topic": "Recent Request Status",
                        "source_agent": "VIGBOT (Status Engine)",
                        "redirect_path": "services",
                        "action": {
                            "type": "navigate",
                            "label": "Track in Student Services",
                            "target": "services",
                            "route": "/?tab=services"
                        },
                        "structured_card": None,
                        "citations": [],
                        "routed_by": "universal_nlu"
                    }

            return {
                "content": (
                    "To track the status of your applications or service requests, please visit the **Student Services** tab.\n"
                    "You can view all live ticket updates, assigned administrative desks, and resolution notes there."
                ),
                "category": "SERVICES",
                "topic": "Status Tracking",
                "source_agent": "VIGBOT (Status Engine)",
                "redirect_path": "services",
                "action": {
                    "type": "navigate",
                    "label": "Open Student Services",
                    "target": "services",
                    "route": "/?tab=services"
                },
                "structured_card": None,
                "citations": [],
                "routed_by": "universal_nlu"
            }

        # -------------------------------------------------------------------
        # 3. AMBIGUOUS QUERIES: Ask for targeted clarification
        # -------------------------------------------------------------------
        if comm_intent == CommunicationIntent.AMBIGUOUS:
            q_lower = query.lower()
            if "found" in q_lower or "lost" in q_lower:
                return {
                    "content": (
                        "It sounds like you have a question regarding a lost or found item on campus!\n\n"
                        "• If you **found an item**: You can report it in the **Lost & Found** section so the owner can claim it.\n"
                        "• If you **lost an item**: You can check current listings or submit a lost item alert.\n\n"
                        "Would you like me to open the **Lost & Found** section for you?"
                    ),
                    "category": "LOST_AND_FOUND",
                    "topic": "Lost & Found Guidance",
                    "source_agent": "VIGBOT (Navigation Assistant)",
                    "redirect_path": "lost-and-found",
                    "action": {
                        "type": "navigate",
                        "label": "Open Lost & Found",
                        "target": "lost-and-found",
                        "route": "/?tab=lost-and-found"
                    },
                    "structured_card": {
                        "type": "navigation",
                        "title": "Lost & Found Section",
                        "subtitle": "Report or claim misplaced campus belongings",
                        "badge": "Feature Discovery",
                        "badgeVariant": "blue",
                        "actionLabel": "Open Lost & Found",
                        "actionIntent": "navigate:lost-and-found",
                        "target": "lost-and-found"
                    },
                    "citations": [],
                    "routed_by": "universal_nlu"
                }

            return {
                "content": (
                    "I want to make sure I direct you to the right place. Could you please specify what you need assistance with?\n\n"
                    "• **Lost & Found:** Report or claim lost belongings on campus.\n"
                    "• **Student Services:** Apply for certificates, ID cards, or official documents.\n"
                    "• **Grievances:** Lodge a formal concern regarding academics or campus life.\n"
                    "• **Academics:** Attendance, marks, timetable, or subject tutoring."
                ),
                "category": "HELP",
                "topic": "Intent Clarification",
                "source_agent": "VIGBOT (Navigation Assistant)",
                "redirect_path": None,
                "action": None,
                "structured_card": None,
                "citations": [],
                "routed_by": "universal_nlu"
            }

        # -------------------------------------------------------------------
        # 4. CAPABILITY MATCH RESOLUTION (28 Application Capabilities)
        # -------------------------------------------------------------------
        if matching_cap:
            cap_id = matching_cap["feature_id"]
            cap_name = matching_cap["name"]
            frontend_tab = matching_cap["frontend_tab"]
            guidance = matching_cap["guidance_text"]
            nav_label = matching_cap["default_navigation_label"]

            # Scenario A: Information Request (ASKING: Where, How, Timings, Rules)
            # STRICT FALSE-ACTION GUARD: NEVER write to DB or fabricate tickets!
            if comm_intent == CommunicationIntent.INFORMATION_REQUEST:
                # Statutory Anti-Ragging Special Notice
                if cap_id == "grievance" and any(k in query.lower() for k in ["ragging", "anti-ragging", "antiragging"]):
                    content_text = (
                        "🚨 **Statutory Anti-Ragging Notice (Zero-Tolerance Policy):**\n"
                        "Vignan University enforces a strict zero-tolerance policy towards ragging in compliance with UGC Regulations.\n\n"
                        "**Immediate Emergency Contacts:**\n"
                        "• **National Anti-Ragging Helpline:** `1800-180-5522` (24x7 Toll-Free)\n"
                        "• **Helpline Email:** `helpline@antiragging.in`\n"
                        "• **University Anti-Ragging Squad / Proctor Office:** Admin Block, Room 101\n\n"
                        "You can also submit an official confidential complaint directly via the Student Grievance portal below."
                    )
                elif cap_id == "map":
                    from app.agent.tool_registry import ToolRegistry
                    tool_res = ToolRegistry.get_campus_location_and_navigation(destination=query)
                    direct_ans = tool_res.get("direct_answer", "")
                    data = tool_res.get("data")
                    if data and isinstance(data, dict) and "steps" in data:
                        steps_lines = "\n".join(f"• {s}" for s in data["steps"])
                        b_name = data.get("destination", "Target Block")
                        b_dist = data.get("total_distance_meters", 0.0)
                        origin = data.get("origin", "Main Gate")
                        content_text = (
                            f"📍 **{b_name} Location & Campus Directions:**\n\n"
                            f"{direct_ans}\n\n"
                            f"**🚶 Turn-by-Turn Walking Route from {origin} ({b_dist}m):**\n"
                            f"{steps_lines}\n\n"
                            f"You can also explore the interactive 2D layout in the **Campus Map** tab."
                        )
                    else:
                        content_text = f"{direct_ans}\n\nYou can explore the interactive building layout on the **Campus Map** tab."

                    return {
                        "content": content_text,
                        "category": "MAP",
                        "topic": f"Campus Navigation: {data.get('destination', 'Campus Map') if (data and isinstance(data, dict)) else 'Campus Map'}",
                        "source_agent": "VIGBOT (Campus Spatial Guide)",
                        "redirect_path": "map",
                        "action": {
                            "type": "navigate",
                            "label": "Open Campus Map",
                            "target": "map",
                            "route": "/?tab=map"
                        },
                        "structured_card": {
                            "type": "navigation",
                            "title": "Campus Map & Navigation",
                            "subtitle": "Interactive building map & route planner",
                            "badge": "Spatial Guide",
                            "badgeVariant": "blue",
                            "actionLabel": "Open Campus Map",
                            "actionIntent": "navigate:map",
                            "target": "map"
                        },
                        "suggested_follow_ups": ["Where is A-Block?", "Where is U-Block?", "How to reach NTR Library?"],
                        "citations": ["VFSTR Campus Spatial Directory", "Campus Navigation Graph (Dijkstra)"],
                        "routed_by": "universal_nlu"
                    }
                else:
                    content_text = f"{guidance}\n\nYou can access it directly using the button below."

                return {
                    "content": content_text,
                    "category": matching_cap["category"],
                    "topic": f"{cap_name} Guidance",
                    "source_agent": "VIGBOT (Feature Navigation Assistant)",
                    "redirect_path": frontend_tab,
                    "action": {
                        "type": "navigate",
                        "label": nav_label,
                        "target": frontend_tab,
                        "route": matching_cap["frontend_route"]
                    },
                    "structured_card": {
                        "type": "navigation",
                        "title": cap_name,
                        "subtitle": matching_cap["description"],
                        "badge": "Application Feature",
                        "badgeVariant": "blue",
                        "actionLabel": nav_label,
                        "actionIntent": f"navigate:{frontend_tab}",
                        "target": frontend_tab
                    },
                    "citations": [],
                    "routed_by": "universal_nlu"
                }

            # Scenario B: Direct Navigation Request ("Open Lost & Found", "Take me there", "kholo")
            if comm_intent == CommunicationIntent.NAVIGATION_REQUEST:
                return {
                    "content": f"Opening **{cap_name}** for you now.",
                    "category": matching_cap["category"],
                    "topic": f"Navigate to {cap_name}",
                    "source_agent": "VIGBOT (Navigation Assistant)",
                    "redirect_path": frontend_tab,
                    "action": {
                        "type": "navigate",
                        "label": nav_label,
                        "target": frontend_tab,
                        "route": matching_cap["frontend_route"]
                    },
                    "structured_card": {
                        "type": "navigation",
                        "title": cap_name,
                        "subtitle": f"Switching to {cap_name} view",
                        "badge": "Navigation",
                        "badgeVariant": "green",
                        "actionLabel": nav_label,
                        "actionIntent": f"navigate:{frontend_tab}",
                        "target": frontend_tab
                    },
                    "citations": [],
                    "routed_by": "universal_nlu"
                }

            # Scenario C: Action Request (DOING: User wants to submit, report, book, apply)
            if comm_intent == CommunicationIntent.ACTION_REQUEST:
                # Genuine student services requests (e.g. bonafide certificate, duplicate ID card)
                # are dispatched to the specialized services tool in NLUEngine to generate legitimate verified tickets.
                if cap_id == "services":
                    return None

                # For Lost & Found reporting: guide user to official reporting modal with prefill instructions
                if cap_id == "lost-and-found":
                    return {
                        "content": (
                            "To report an item you found, please open the **Lost & Found** section and click the **'Report Item'** button.\n\n"
                            "You will be able to enter:\n"
                            "1. Item title (e.g. 'Blue Dell Laptop Bag')\n"
                            "2. Category & where it was found (e.g. 'U-Block Room 204')\n"
                            "3. Your contact info or where you deposited the item.\n\n"
                            "Click below to open the reporting screen."
                        ),
                        "category": "LOST_AND_FOUND",
                        "topic": "Report Found Item",
                        "source_agent": "VIGBOT (Lost & Found Assistant)",
                        "redirect_path": "lost-and-found",
                        "action": {
                            "type": "navigate",
                            "label": "Open Lost & Found Form",
                            "target": "lost-and-found",
                            "route": "/?tab=lost-and-found"
                        },
                        "structured_card": {
                            "type": "navigation",
                            "title": "Report Found Item",
                            "subtitle": "Click to open the Lost & Found submission form",
                            "badge": "Action Guide",
                            "badgeVariant": "emerald",
                            "actionLabel": "Open Lost & Found",
                            "actionIntent": "navigate:lost-and-found",
                            "target": "lost-and-found"
                        },
                        "citations": [],
                        "routed_by": "universal_nlu"
                    }

                # For Bookings: Guide user to facility booking screen with explicit parameters
                if cap_id == "bookings":
                    return {
                        "content": (
                            "To book a campus facility (Seminar Hall, Auditorium, or Sports Ground):\n\n"
                            "1. Open the **Facility Booking** section.\n"
                            "2. Select your desired facility and date.\n"
                            "3. Choose an available time slot and state the academic event purpose.\n\n"
                            "Click below to reserve your slot."
                        ),
                        "category": "BOOKINGS",
                        "topic": "Facility Reservation",
                        "source_agent": "VIGBOT (Bookings Assistant)",
                        "redirect_path": "bookings",
                        "action": {
                            "type": "navigate",
                            "label": "Open Facility Bookings",
                            "target": "bookings",
                            "route": "/?tab=bookings"
                        },
                        "structured_card": {
                            "type": "navigation",
                            "title": "Facility Reservation",
                            "subtitle": "Reserve campus venues and seminar halls",
                            "badge": "Action Required",
                            "badgeVariant": "blue",
                            "actionLabel": "Open Bookings",
                            "actionIntent": "navigate:bookings",
                            "target": "bookings"
                        },
                        "citations": [],
                        "routed_by": "universal_nlu"
                    }

                # Other action-capable features: guide user to official modal without fabricating tickets
                return {
                    "content": (
                        f"To proceed with your request for **{cap_name}**, please use the official form in the {cap_name} section.\n"
                        f"Click below to navigate directly to the workspace."
                    ),
                    "category": matching_cap["category"],
                    "topic": f"{cap_name} Action",
                    "source_agent": "VIGBOT (Action Assistant)",
                    "redirect_path": frontend_tab,
                    "action": {
                        "type": "navigate",
                        "label": f"Open {cap_name}",
                        "target": frontend_tab,
                        "route": matching_cap["frontend_route"]
                    },
                    "structured_card": {
                        "type": "navigation",
                        "title": cap_name,
                        "subtitle": f"Open the {cap_name} workspace",
                        "badge": "Action Required",
                        "badgeVariant": "blue",
                        "actionLabel": f"Open {cap_name}",
                        "actionIntent": f"navigate:{frontend_tab}",
                        "target": frontend_tab
                    },
                    "citations": [],
                    "routed_by": "universal_nlu"
                }

        # If not matching a specific frontend capability, return None to let standard NLU proceed
        return None
