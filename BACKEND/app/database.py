import uuid
import datetime
import os
import sqlite3
import json
from typing import Dict, Any, List, Optional
from app.config import settings
def is_postgres_configured() -> bool:
    if getattr(settings, "USE_IN_MEMORY_DB", False):
        return False
    db_url = (getattr(settings, "DATABASE_URL", "") or "").strip()
    if "localhost:5432" in db_url or "127.0.0.1:5432" in db_url:
        return False
    return db_url.startswith("postgresql://") or db_url.startswith("postgres://") or "+psycopg" in db_url

def get_db_connection():
    if is_postgres_configured():
        db_url = getattr(settings, "DATABASE_URL", "")
        cleaned_url = db_url.replace("postgresql+psycopg://", "postgresql://")
        try:
            import psycopg
            from psycopg.rows import dict_row
            return psycopg.connect(cleaned_url, row_factory=dict_row, connect_timeout=3)
        except Exception:
            try:
                import psycopg2
                import psycopg2.extras
                return psycopg2.connect(cleaned_url, cursor_factory=psycopg2.extras.RealDictCursor, connect_timeout=3)
            except Exception:
                pass

    db_vigbot = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "database", "vigbot.db"))
    db_fallback = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "database", "vigbot.db"))
    db_path = db_vigbot if os.path.exists(db_vigbot) else db_fallback
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS crisis_escalations (
            crisis_escalation_id TEXT PRIMARY KEY,
            student_id TEXT,
            student_name TEXT,
            roll_no TEXT,
            detected_at TEXT,
            detected_by TEXT,
            trigger_snippet TEXT,
            escalated_to TEXT,
            channel_used TEXT,
            status TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analytics_daily (
            stat_date TEXT,
            intent_category TEXT,
            topic TEXT,
            language_code TEXT DEFAULT 'en',
            query_count INTEGER DEFAULT 1,
            successful_answers INTEGER DEFAULT 1,
            escalated_count INTEGER DEFAULT 0,
            distress_count INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS message_feedback (
            feedback_id TEXT PRIMARY KEY,
            message_id TEXT,
            conversation_id TEXT,
            student_id TEXT,
            rating TEXT,
            comment TEXT,
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS faculty (
            faculty_id TEXT PRIMARY KEY,
            employee_no TEXT UNIQUE,
            name TEXT NOT NULL,
            designation TEXT NOT NULL,
            department TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            cabin TEXT NOT NULL,
            role TEXT NOT NULL,
            office_hours TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS campus_locations (
            location_id TEXT PRIMARY KEY,
            room_number TEXT NOT NULL,
            block TEXT NOT NULL,
            floor TEXT NOT NULL,
            description TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fresher_faqs (
            faq_id TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            keywords TEXT
        )
    """)
    conn.commit()
    return conn

class DatabaseSession:
    """
    A context-scoped database session that enforces Row-Level Security (RLS).
    The session holds the verified student_id and user_id.
    Queries executed through this session strictly enforce the student boundary.
    """
    def __init__(self, student_id: Optional[str] = None, user_id: Optional[str] = None):
        self.student_id = student_id
        self.user_id = user_id

class DataRepository:
    """
    Data repository providing strictly row-level secured access to all student records
    using SQLite or PostgreSQL database directly.
    """
    
    @staticmethod
    def _execute_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        with get_db_connection() as conn:
            if isinstance(conn, sqlite3.Connection):
                cur = conn.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
            else:
                query_pg = query.replace("?", "%s")
                with conn.cursor() as cur:
                    cur.execute(query_pg, params)
                    return [dict(row) for row in cur.fetchall()]

    @staticmethod
    def _execute_insert(query: str, params: tuple = ()):
        with get_db_connection() as conn:
            if isinstance(conn, sqlite3.Connection):
                conn.execute(query, params)
                conn.commit()
            else:
                query_pg = query.replace("?", "%s")
                with conn.cursor() as cur:
                    cur.execute(query_pg, params)
                conn.commit()

    @staticmethod
    def _resolve_student_id(session: DatabaseSession) -> Optional[str]:
        if not session or not session.student_id:
            return None
        res = DataRepository._execute_query(
            "SELECT student_id FROM students WHERE student_id = ? OR roll_no = ? LIMIT 1",
            (session.student_id, session.student_id)
        )
        if res:
            return res[0]["student_id"]
        return session.student_id

    @staticmethod
    def get_student_by_username(username: str) -> Optional[Dict[str, Any]]:
        clean_user = username.lower().replace("-", "").replace(" ", "")
        # Can't do easy replace in SQL across all formats, so fetch all and filter or do OR
        query = "SELECT * FROM students WHERE LOWER(REPLACE(REPLACE(username, '-', ''), ' ', '')) = ? OR LOWER(REPLACE(REPLACE(roll_no, '-', ''), ' ', '')) = ? OR LOWER(REPLACE(REPLACE(student_id, '-', ''), ' ', '')) = ?"
        res = DataRepository._execute_query(query, (clean_user, clean_user, clean_user))
        return res[0] if res else None

    @staticmethod
    def get_student_profile(session: DatabaseSession) -> Optional[Dict[str, Any]]:
        sid = DataRepository._resolve_student_id(session)
        if not sid:
            return None
        res = DataRepository._execute_query("SELECT * FROM students WHERE student_id = ?", (sid,))
        return res[0] if res else None

    @staticmethod
    def get_student_advisors(session: DatabaseSession) -> Optional[Dict[str, Any]]:
        profile = DataRepository.get_student_profile(session)
        if not profile:
            return None
        return {
            "student_id": profile.get("student_id"),
            "roll_no": profile.get("roll_no"),
            "full_name": profile.get("full_name"),
            "class_teacher": {
                "name": profile.get("class_teacher_name") or "Not Assigned",
                "phone": profile.get("class_teacher_phone") or "",
                "email": profile.get("class_teacher_email") or "",
                "cabin": profile.get("class_teacher_cabin") or "Not Assigned"
            },
            "counsellor": {
                "name": profile.get("counsellor_name") or "Not Assigned",
                "phone": profile.get("counsellor_phone") or "",
                "email": profile.get("counsellor_email") or "",
                "cabin": profile.get("counsellor_cabin") or "Not Assigned"
            },
            "mentor": {
                "name": profile.get("mentor_name") or profile.get("class_teacher_name") or "Not Assigned",
                "phone": profile.get("mentor_phone") or "",
                "email": profile.get("mentor_email") or "",
                "cabin": profile.get("mentor_cabin") or "Not Assigned"
            },
            "hod": {
                "name": profile.get("hod_name") or "Not Assigned",
                "phone": profile.get("hod_phone") or "",
                "email": profile.get("hod_email") or ""
            }
        }

    @staticmethod
    def get_faculty_directory(session: Optional[DatabaseSession] = None) -> List[Dict[str, Any]]:
        return DataRepository._execute_query("SELECT * FROM faculty ORDER BY name ASC")

    @staticmethod
    def get_subject_faculty(session: DatabaseSession, subject_query: Optional[str] = None) -> List[Dict[str, Any]]:
        att = DataRepository.get_attendance(session, subject_query)
        res = []
        seen = set()
        for a in att:
            c_code = a.get("course_code")
            if c_code not in seen:
                seen.add(c_code)
                fac_name = a.get("faculty_name", "")
                clean_name = fac_name.split("(")[0].strip()
                fac_row = DataRepository._execute_query("SELECT * FROM faculty WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?", (f"%{clean_name.lower()}%", f"%{clean_name.split()[-1].lower()}%"))
                f_info = fac_row[0] if fac_row else {}
                phone = f_info.get("phone")
                if not phone and "(" in fac_name and any(c.isdigit() for c in fac_name):
                    phone = "+91 " + fac_name.split("(")[1].split(")")[0]
                cabin = f_info.get("cabin") or "Not Assigned"
                res.append({
                    "course_code": c_code,
                    "course_title": a.get("course_title"),
                    "faculty_name": f_info.get("name") or clean_name,
                    "phone": phone or "",
                    "email": f_info.get("email") or "",
                    "cabin": cabin,
                    "cabin_location": cabin,
                    "designation": f_info.get("designation") or "Faculty Member"
                })
        return res

    @staticmethod
    def get_attendance(session: DatabaseSession, subject_query: Optional[str] = None) -> List[Dict[str, Any]]:
        sid = DataRepository._resolve_student_id(session)
        query = "SELECT * FROM attendance WHERE student_id = ?"
        params = [sid]
        if subject_query:
            query += " AND (LOWER(course_code) LIKE ? OR LOWER(course_title) LIKE ?)"
            like_val = f"%{subject_query.lower()}%"
            params.extend([like_val, like_val])
        return DataRepository._execute_query(query, tuple(params))

    @staticmethod
    def get_timetable(session: DatabaseSession, day: Optional[str] = None) -> List[Dict[str, Any]]:
        sid = DataRepository._resolve_student_id(session)
        query = "SELECT * FROM timetable WHERE student_id = ?"
        params = [sid]
        if day:
            query += " AND LOWER(day_of_week) = ?"
            params.append(day.lower())
        return DataRepository._execute_query(query, tuple(params))

    @staticmethod
    def get_marks(session: DatabaseSession, subject_query: Optional[str] = None) -> List[Dict[str, Any]]:
        sid = DataRepository._resolve_student_id(session)
        query = "SELECT * FROM marks WHERE student_id = ?"
        params = [sid]
        if subject_query:
            query += " AND (LOWER(course_code) LIKE ? OR LOWER(course_title) LIKE ?)"
            like_val = f"%{subject_query.lower()}%"
            params.extend([like_val, like_val])
        return DataRepository._execute_query(query, tuple(params))

    @staticmethod
    def get_exams(session: DatabaseSession) -> List[Dict[str, Any]]:
        sid = DataRepository._resolve_student_id(session)
        return DataRepository._execute_query("SELECT * FROM exams WHERE student_id = ?", (sid,))

    @staticmethod
    def get_fees(session: DatabaseSession) -> Optional[Dict[str, Any]]:
        sid = DataRepository._resolve_student_id(session)
        res = DataRepository._execute_query("SELECT * FROM fees WHERE student_id = ?", (sid,))
        return res[0] if res else None

    @staticmethod
    def get_library_lended_books(session: DatabaseSession) -> List[Dict[str, Any]]:
        sid = DataRepository._resolve_student_id(session)
        return DataRepository._execute_query("SELECT * FROM library_lended_books WHERE student_id = ?", (sid,))


    @staticmethod
    def get_curriculum(session: DatabaseSession) -> Optional[Dict[str, Any]]:
        res = DataRepository._execute_query("SELECT * FROM curriculum LIMIT 1")
        if res:
            data = res[0]
            if isinstance(data.get("next_semester_courses"), str):
                try:
                    data["next_semester_courses"] = json.loads(data["next_semester_courses"])
                except:
                    pass
            return data
        return None

    @staticmethod
    def get_campus_location(room_number: str) -> Optional[Dict[str, Any]]:
        try:
            query = "SELECT * FROM campus_locations WHERE LOWER(room_number) = ?"
            res = DataRepository._execute_query(query, (room_number.lower(),))
            return res[0] if res else None
        except Exception:
            return None

    @staticmethod
    def search_fresher_faqs(query_text: str) -> List[Dict[str, Any]]:
        try:
            faqs = DataRepository._execute_query("SELECT * FROM fresher_faqs")
        except Exception:
            return []
        import re
        words = set(re.findall(r'\b\w+\b', query_text.lower()))
        
        best_faq = None
        best_score = 0
        
        for faq in faqs:
            text = (faq['topic'] + " " + faq['question'] + " " + faq['answer'] + " " + faq['keywords']).lower()
            score = 0
            for w in words:
                if len(w) > 3 and w in text:
                    score += 1
                elif w in ['mhp', 'zest', 'sac', 'fee', 'id']:
                    if w in text:
                        score += 5
            
            if score > best_score:
                best_score = score
                best_faq = faq
                
        return [best_faq] if best_faq and best_score > 0 else []

    @staticmethod
    def search_policies(query_text: str) -> List[Dict[str, Any]]:
        try:
            query = "SELECT * FROM policies WHERE LOWER(title) LIKE ? OR LOWER(summary) LIKE ?"
            like_val = f"%{query_text.lower()}%"
            matches = DataRepository._execute_query(query, (like_val, like_val))
            if not matches:
                return DataRepository._execute_query("SELECT * FROM policies LIMIT 2")
            return matches
        except Exception:
            return []

    @staticmethod
    def search_circulars(query_text: str) -> List[Dict[str, Any]]:
        try:
            query = "SELECT * FROM circulars WHERE LOWER(title) LIKE ? OR LOWER(summary) LIKE ?"
            like_val = f"%{query_text.lower()}%"
            matches = DataRepository._execute_query(query, (like_val, like_val))
            if not matches:
                return DataRepository._execute_query("SELECT * FROM circulars LIMIT 2")
            return matches
        except Exception:
            return []

    @staticmethod
    def list_conversations(session: DatabaseSession) -> List[Dict[str, Any]]:
        return DataRepository._execute_query("SELECT * FROM conversations WHERE student_id = ? ORDER BY updated_at DESC", (session.student_id,))

    @staticmethod
    def get_conversation(session: DatabaseSession, conversation_id: str) -> Optional[Dict[str, Any]]:
        res = DataRepository._execute_query("SELECT * FROM conversations WHERE conversation_id = ? AND student_id = ?", (conversation_id, session.student_id))
        if res:
            data = res[0]
            if isinstance(data.get("context_data"), str):
                try: data["context_data"] = json.loads(data["context_data"])
                except: pass
            return data
        return None

    @staticmethod
    def update_conversation_context(session: DatabaseSession, conversation_id: str, context_data: Dict[str, Any]) -> None:
        """Persist conversation memory while enforcing the authenticated student boundary."""
        DataRepository._execute_insert(
            "UPDATE conversations SET context_data = ?, updated_at = ? WHERE conversation_id = ? AND student_id = ?",
            (json.dumps(context_data), datetime.datetime.now(datetime.timezone.utc).isoformat(), conversation_id, session.student_id)
        )

    @staticmethod
    def create_conversation(session: DatabaseSession, title: str) -> Dict[str, Any]:
        conv_id = f"conv-{uuid.uuid4().hex[:8]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        query = "INSERT INTO conversations (conversation_id, student_id, title, status, context_data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)"
        DataRepository._execute_insert(query, (conv_id, session.student_id, title or "New Conversation", "ACTIVE", "{}", now, now))
        return DataRepository.get_conversation(session, conv_id)

    @staticmethod
    def get_conversation_messages(session: DatabaseSession, conversation_id: str) -> List[Dict[str, Any]]:
        conv = DataRepository.get_conversation(session, conversation_id)
        if not conv:
            return []
        msgs = DataRepository._execute_query("SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC", (conversation_id,))
        for m in msgs:
            if isinstance(m.get("citations"), str):
                try: m["citations"] = json.loads(m["citations"])
                except: pass
            if isinstance(m.get("structured_card"), str):
                try: m["structured_card"] = json.loads(m["structured_card"])
                except: pass
        return msgs

    @staticmethod
    def add_message(session: DatabaseSession, conversation_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        conv = DataRepository.get_conversation(session, conversation_id)
        if not conv:
            raise PermissionError("Access denied: conversation does not belong to the authenticated student.")
        
        msg_id = f"msg-{uuid.uuid4().hex[:8]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        citations = json.dumps(message_data.get("citations", []))
        structured_card = json.dumps(message_data.get("structured_card")) if message_data.get("structured_card") else None
        
        query = "INSERT INTO messages (message_id, conversation_id, sender_role, content, category, source_agent, citations, structured_card, is_distress, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        DataRepository._execute_insert(query, (msg_id, conversation_id, message_data.get("sender_role", "STUDENT"), message_data.get("content"), message_data.get("category"), message_data.get("source_agent", "VIGBOT"), citations, structured_card, 1 if message_data.get("is_distress") else 0, now))
        
        DataRepository._execute_insert("UPDATE conversations SET updated_at = ? WHERE conversation_id = ?", (now, conversation_id))
        
        res = DataRepository._execute_query("SELECT * FROM messages WHERE message_id = ?", (msg_id,))
        m = res[0]
        if isinstance(m.get("citations"), str):
            try: m["citations"] = json.loads(m["citations"])
            except: pass
        if isinstance(m.get("structured_card"), str):
            try: m["structured_card"] = json.loads(m["structured_card"])
            except: pass
        return m

    @staticmethod
    def create_service_request(session: DatabaseSession, data: Dict[str, Any]) -> Dict[str, Any]:
        req_id = f"sr-{uuid.uuid4().hex[:8]}"
        count_res = DataRepository._execute_query("SELECT COUNT(*) as c FROM service_requests")
        req_no = f"SR-2026-{(count_res[0]['c'] + 1):04d}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        sla = (datetime.date.today() + datetime.timedelta(days=3)).isoformat()
        
        sid = DataRepository._resolve_student_id(session)
        query = "INSERT INTO service_requests (service_request_id, request_no, student_id, category, title, description, priority, status, assigned_office, sla_due_date, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        DataRepository._execute_insert(query, (req_id, req_no, sid, data["category"], data["title"], data["description"], data.get("priority", "NORMAL"), "SUBMITTED", "Registrar Student Affairs", sla, now, now))
        
        res = DataRepository._execute_query("SELECT * FROM service_requests WHERE service_request_id = ?", (req_id,))
        return res[0] if res else None

    @staticmethod
    def list_service_requests(session: DatabaseSession) -> List[Dict[str, Any]]:
        sid = DataRepository._resolve_student_id(session)
        return DataRepository._execute_query("SELECT * FROM service_requests WHERE student_id = ?", (sid,))

    @staticmethod
    def create_club_application(session: DatabaseSession, club_id: str, student_name: str) -> Dict[str, Any]:
        sid = DataRepository._resolve_student_id(session)
        # Check if already applied to avoid duplicate entry
        existing = DataRepository._execute_query(
            "SELECT * FROM studentlife_club_application WHERE student_id = ? AND club_id = ? LIMIT 1",
            (sid, club_id)
        )
        if existing:
            return existing[0]
        # Reset PostgreSQL sequence to avoid stale id gaps causing UniqueViolation
        if is_postgres_configured():
            try:
                DataRepository._execute_query(
                    "SELECT setval(COALESCE(pg_get_serial_sequence('studentlife_club_application', 'id'), 'studentlife_club_application_id_seq'), "
                    "COALESCE((SELECT MAX(id) FROM studentlife_club_application), 0) + 1, false)"
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to reset sequence: {e}")
        query = "INSERT INTO studentlife_club_application (club_id, student_name, status, student_id) VALUES (?, ?, ?, ?)"
        DataRepository._execute_insert(query, (club_id, student_name, "Pending", sid))
        res = DataRepository._execute_query(
            "SELECT * FROM studentlife_club_application WHERE student_id = ? ORDER BY id DESC LIMIT 1", (sid,)
        )
        return res[0] if res else None


    @staticmethod
    def get_clubs() -> List[Dict[str, Any]]:
        try:
            return DataRepository._execute_query("SELECT * FROM studentlife_club")
        except Exception:
            return []

    @staticmethod
    def get_all_faqs() -> List[Dict[str, Any]]:
        try:
            return DataRepository._execute_query("SELECT * FROM fresher_faqs")
        except Exception:
            return []

    @staticmethod
    def get_all_policies() -> List[Dict[str, Any]]:
        try:
            return DataRepository._execute_query("SELECT * FROM policies")
        except Exception:
            return []

    @staticmethod
    def get_all_circulars() -> List[Dict[str, Any]]:
        try:
            return DataRepository._execute_query("SELECT * FROM circulars ORDER BY issued_date DESC")
        except Exception:
            return []

    @staticmethod
    def get_facilities() -> List[Dict[str, Any]]:
        try:
            return DataRepository._execute_query("SELECT * FROM facilities")
        except Exception:
            return []

    @staticmethod
    def get_transport_routes() -> List[Dict[str, Any]]:
        try:
            return DataRepository._execute_query("SELECT * FROM transportation_routes")
        except Exception:
            return []

    @staticmethod
    def get_wellness_resources() -> List[Dict[str, Any]]:
        try:
            return DataRepository._execute_query("SELECT * FROM wellness_resources")
        except Exception:
            return []

    @staticmethod
    def get_library_resources() -> List[Dict[str, Any]]:
        try:
            return DataRepository._execute_query("SELECT * FROM library_resources LIMIT 20")
        except Exception:
            return []

    @staticmethod
    def get_campus_locations() -> List[Dict[str, Any]]:
        try:
            return DataRepository._execute_query("SELECT * FROM campus_locations")
        except Exception:
            return []

    @staticmethod
    def get_broadcast_alerts() -> List[Dict[str, Any]]:
        try:
            return DataRepository._execute_query("SELECT * FROM broadcast_alerts WHERE is_active = TRUE ORDER BY timestamp DESC LIMIT 5")
        except Exception:
            return []

    @staticmethod
    def get_lost_and_found() -> List[Dict[str, Any]]:
        try:
            return DataRepository._execute_query("SELECT * FROM lost_and_found ORDER BY date_reported DESC LIMIT 10")
        except Exception:
            return []

    @staticmethod
    def get_upcoming_events() -> List[Dict[str, Any]]:
        try:
            return DataRepository._execute_query("SELECT * FROM calendar_events ORDER BY start_time ASC LIMIT 10")
        except Exception:
            return []

    @staticmethod
    def log_crisis_escalation(session: DatabaseSession, trigger_phrase: str, student_info: Dict[str, Any]) -> Dict[str, Any]:
        esc_id = f"esc-{uuid.uuid4().hex[:8]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        query = "INSERT INTO crisis_escalations (crisis_escalation_id, student_id, student_name, roll_no, detected_at, detected_by, trigger_snippet, escalated_to, channel_used, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        DataRepository._execute_insert(query, (esc_id, session.student_id, student_info.get("full_name"), student_info.get("roll_no"), now, "VIGBOT Distress Guardrail", trigger_phrase, "24/7 Student Wellbeing Helpline & On-duty Counselor", "PRIORITY_INTERNAL_DISPATCH", "PAGE_SENT"))
        
        res = DataRepository._execute_query("SELECT * FROM crisis_escalations WHERE crisis_escalation_id = ?", (esc_id,))
        return res[0] if res else None

    @staticmethod
    def record_query_metric(intent_category: str, topic: str, language: str = "en", is_distress: bool = False, is_escalated: bool = False):
        today_str = datetime.date.today().isoformat()
        try:
            existing = DataRepository._execute_query("SELECT * FROM analytics_daily WHERE stat_date = ? AND intent_category = ? AND topic = ? AND language_code = ?", (today_str, intent_category, topic, language))
            if existing:
                query = "UPDATE analytics_daily SET query_count = query_count + 1, successful_answers = successful_answers + 1, distress_count = distress_count + ?, escalated_count = escalated_count + ? WHERE stat_date = ? AND intent_category = ? AND topic = ? AND language_code = ?"
                DataRepository._execute_insert(query, (1 if is_distress else 0, 1 if is_escalated else 0, today_str, intent_category, topic, language))
            else:
                query = "INSERT INTO analytics_daily (stat_date, intent_category, topic, language_code, query_count, successful_answers, escalated_count, distress_count) VALUES (?, ?, ?, ?, 1, 1, ?, ?)"
                DataRepository._execute_insert(query, (today_str, intent_category, topic, language, 1 if is_escalated else 0, 1 if is_distress else 0))
        except Exception:
            pass

    @staticmethod
    def get_analytics_summary() -> List[Dict[str, Any]]:
        return DataRepository._execute_query("SELECT * FROM analytics_daily")

    @staticmethod
    def record_message_feedback(
        session: DatabaseSession,
        conversation_id: str,
        message_id: str,
        rating: str,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        conv = DataRepository.get_conversation(session, conversation_id)
        if not conv:
            raise PermissionError("Access denied: conversation does not belong to the authenticated student.")
        
        fb_id = f"fb-{uuid.uuid4().hex[:8]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        query = "INSERT INTO message_feedback (feedback_id, message_id, conversation_id, student_id, rating, comment, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)"
        DataRepository._execute_insert(query, (fb_id, message_id, conversation_id, session.student_id, rating, comment or "", now))
        return {
            "feedback_id": fb_id,
            "message_id": message_id,
            "conversation_id": conversation_id,
            "rating": rating,
            "comment": comment,
            "created_at": now
        }

    @staticmethod
    def get_message_by_id(session: DatabaseSession, message_id: str) -> Optional[Dict[str, Any]]:
        msgs = DataRepository._execute_query("SELECT * FROM messages WHERE message_id = ?", (message_id,))
        if not msgs:
            return None
        m = msgs[0]
        conv = DataRepository.get_conversation(session, m["conversation_id"])
        if not conv:
            return None
        if isinstance(m.get("citations"), str):
            try: m["citations"] = json.loads(m["citations"])
            except: pass
        if isinstance(m.get("structured_card"), str):
            try: m["structured_card"] = json.loads(m["structured_card"])
            except: pass
        return m


class _CrisisEscalationsProxy:
    """Compatibility proxy so tests can inspect CRISIS_ESCALATIONS_DB directly."""
    def __len__(self):
        return len(DataRepository._execute_query("SELECT * FROM crisis_escalations"))
    def __getitem__(self, idx):
        return DataRepository._execute_query("SELECT * FROM crisis_escalations")[idx]
    def __iter__(self):
        return iter(DataRepository._execute_query("SELECT * FROM crisis_escalations"))

class _AnalyticsDailyProxy:
    """Compatibility proxy so tests can inspect ANALYTICS_DAILY_DB directly."""
    def __len__(self):
        return len(DataRepository._execute_query("SELECT * FROM analytics_daily"))
    def __getitem__(self, idx):
        return DataRepository._execute_query("SELECT * FROM analytics_daily")[idx]
    def __iter__(self):
        return iter(DataRepository._execute_query("SELECT * FROM analytics_daily"))

CRISIS_ESCALATIONS_DB = _CrisisEscalationsProxy()
ANALYTICS_DAILY_DB = _AnalyticsDailyProxy()

class _StudentsDbProxy(dict):
    def values(self):
        return DataRepository._execute_query("SELECT * FROM students")
    def __getitem__(self, key):
        s = DataRepository.get_student_by_username(str(key))
        if s:
            return s
        raise KeyError(key)

STUDENTS_DB = _StudentsDbProxy()
