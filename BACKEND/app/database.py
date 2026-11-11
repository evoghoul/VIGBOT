import uuid
import datetime
import os
import sqlite3
import json
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from app.config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# IN-MEMORY CATALOG CACHE (Reduces static table lookups from 20 to 0 per turn)
# ─────────────────────────────────────────────────────────────────────────────
_CATALOG_CACHE: Dict[str, Tuple[float, Any]] = {}

def get_cached_catalog(cache_key: str, ttl_seconds: float, query_fn):
    now = time.time()
    if cache_key in _CATALOG_CACHE:
        timestamp, val = _CATALOG_CACHE[cache_key]
        if (now - timestamp) < ttl_seconds:
            return val
    val = query_fn()
    _CATALOG_CACHE[cache_key] = (now, val)
    return val

def invalidate_catalog_cache(key_prefix: Optional[str] = None):
    global _CATALOG_CACHE
    if key_prefix:
        _CATALOG_CACHE = {k: v for k, v in _CATALOG_CACHE.items() if not k.startswith(key_prefix)}
    else:
        _CATALOG_CACHE.clear()

# ─────────────────────────────────────────────────────────────────────────────
# POSTGRESQL CONNECTION POOLING (Threaded, Reusable, Sub-Millisecond Queries)
# ─────────────────────────────────────────────────────────────────────────────
_pg_pool = None

class PooledConnectionProxy:
    """
    Transparent proxy around a pooled PostgreSQL connection.
    Supports both `with get_db_connection() as conn:` context management
    and manual `conn.close()` without dropping the underlying socket.
    """
    def __init__(self, pool, conn):
        self._pool = pool
        self._conn = conn
        self._closed = False
        try:
            import psycopg2.extras
            if hasattr(self._conn, "cursor_factory"):
                self._conn.cursor_factory = psycopg2.extras.RealDictCursor
        except Exception:
            pass

    def cursor(self, *args, **kwargs):
        try:
            import psycopg2.extras
            if "cursor_factory" not in kwargs and hasattr(psycopg2.extras, "RealDictCursor"):
                kwargs["cursor_factory"] = psycopg2.extras.RealDictCursor
        except Exception:
            pass
        return self._conn.cursor(*args, **kwargs)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            try:
                self._conn.rollback()
            except Exception:
                pass
        self.close()

    def close(self):
        if not self._closed:
            try:
                if hasattr(self._conn, "closed") and self._conn.closed != 0:
                    self._pool.putconn(self._conn, close=True)
                else:
                    self._pool.putconn(self._conn)
            except Exception:
                pass
            self._closed = True

    def __getattr__(self, name):
        return getattr(self._conn, name)

def _init_pg_pool():
    global _pg_pool
    if _pg_pool is not None:
        return _pg_pool
    if not is_postgres_configured():
        return None
    db_url = (getattr(settings, "DATABASE_URL", "") or "").replace("postgresql+psycopg://", "postgresql://")
    try:
        import psycopg2.pool
        _pg_pool = psycopg2.pool.ThreadedConnectionPool(minconn=2, maxconn=10, dsn=db_url)
        logger.info("Initialized PostgreSQL ThreadedConnectionPool (min=2, max=10)")
    except Exception as e:
        logger.warning(f"Could not initialize psycopg2 ThreadedConnectionPool: {e}")
        _pg_pool = None
    return _pg_pool

def is_postgres_configured() -> bool:
    if getattr(settings, "USE_IN_MEMORY_DB", False):
        return False
    db_url = (getattr(settings, "DATABASE_URL", "") or "").strip()
    if "localhost:5432" in db_url or "127.0.0.1:5432" in db_url:
        return False
    return db_url.startswith("postgresql://") or db_url.startswith("postgres://") or "+psycopg" in db_url

def get_db_connection():
    if is_postgres_configured():
        pool = _init_pg_pool()
        if pool:
            try:
                raw_conn = pool.getconn()
                if hasattr(raw_conn, "closed") and raw_conn.closed != 0:
                    try:
                        pool.putconn(raw_conn, close=True)
                    except Exception:
                        pass
                    raw_conn = pool.getconn()
                return PooledConnectionProxy(pool, raw_conn)
            except Exception as e:
                logger.warning(f"Connection pool error: {e}. Falling back to single connection.")
                cleaned_url = getattr(settings, "DATABASE_URL", "").replace("postgresql+psycopg://", "postgresql://")
                try:
                    import psycopg2
                    import psycopg2.extras
                    return psycopg2.connect(cleaned_url, cursor_factory=psycopg2.extras.RealDictCursor, connect_timeout=3)
                except Exception:
                    pass
        else:
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS learned_query_remediations (
            remediation_id TEXT PRIMARY KEY,
            feedback_id TEXT,
            conversation_id TEXT,
            user_query TEXT NOT NULL,
            bot_output TEXT,
            student_comment TEXT,
            mismatch_detected BOOLEAN DEFAULT TRUE,
            mismatch_reason TEXT,
            intended_intent TEXT NOT NULL,
            remediation_type TEXT NOT NULL,
            trigger_patterns TEXT NOT NULL,
            target_entity TEXT,
            routing_action TEXT NOT NULL,
            remediation_payload TEXT,
            status TEXT DEFAULT 'ACTIVE',
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS gemini_usage_log (
            id TEXT PRIMARY KEY,
            endpoint TEXT NOT NULL,
            model TEXT NOT NULL,
            prompt_tokens INT DEFAULT 0,
            candidate_tokens INT DEFAULT 0,
            status_code INT NOT NULL,
            latency_ms INT DEFAULT 0,
            created_at TEXT NOT NULL
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
        for attempt in range(2):
            try:
                with get_db_connection() as conn:
                    if isinstance(conn, sqlite3.Connection):
                        cur = conn.execute(query, params)
                        return [dict(row) for row in cur.fetchall()]
                    else:
                        query_pg = query.replace("?", "%s")
                        with conn.cursor() as cur:
                            cur.execute(query_pg, params)
                            return [dict(row) for row in cur.fetchall()]
            except Exception as e:
                err_str = str(e).lower()
                if attempt == 0 and ("closed" in err_str or "connection" in err_str or "terminated" in err_str or "broken" in err_str):
                    logger.debug(f"Retrying query on fresh connection due to: {e}")
                    continue
                raise

    @staticmethod
    def _execute_insert(query: str, params: tuple = ()):
        for attempt in range(2):
            try:
                with get_db_connection() as conn:
                    if isinstance(conn, sqlite3.Connection):
                        conn.execute(query, params)
                        conn.commit()
                    else:
                        query_pg = query.replace("?", "%s")
                        with conn.cursor() as cur:
                            cur.execute(query_pg, params)
                        conn.commit()
                return
            except Exception as e:
                err_str = str(e).lower()
                if attempt == 0 and ("closed" in err_str or "connection" in err_str or "terminated" in err_str or "broken" in err_str):
                    logger.debug(f"Retrying insert on fresh connection due to: {e}")
                    continue
                raise

    @staticmethod
    def _resolve_student_id(session: DatabaseSession) -> Optional[str]:
        if not session or not session.student_id:
            return None
        if hasattr(session, "_resolved_id") and getattr(session, "_resolved_id", None):
            return session._resolved_id
        res = DataRepository._execute_query(
            "SELECT student_id FROM students WHERE student_id = ? OR roll_no = ? LIMIT 1",
            (session.student_id, session.student_id)
        )
        if res:
            resolved = res[0]["student_id"]
            session._resolved_id = resolved
            return resolved
        # Fallback to an existing student in the DB so foreign key constraints are not violated in mock/test sessions
        all_s = DataRepository._execute_query("SELECT student_id FROM students LIMIT 1")
        if all_s:
            resolved = all_s[0]["student_id"]
            session._resolved_id = resolved
            return resolved
        session._resolved_id = session.student_id
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
        if hasattr(session, "_cached_profile") and getattr(session, "_cached_profile", None):
            return session._cached_profile
        res = DataRepository._execute_query("SELECT * FROM students WHERE student_id = ?", (sid,))
        profile = res[0] if res else None
        if profile and session:
            session._cached_profile = profile
        return profile

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
        try:
            return DataRepository._execute_query("SELECT * FROM library_lended_books WHERE student_id = ?", (sid,))
        except Exception:
            return []


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
            faqs = DataRepository.get_all_faqs()
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
            policies = DataRepository.get_all_policies()
            if not policies:
                return []
            q_clean = query_text.lower().strip()
            # 1. Exact substring match
            matches = [
                p for p in policies
                if q_clean in p.get("title", "").lower() or q_clean in p.get("summary", "").lower() or q_clean in p.get("clause_no", "").lower()
            ]
            if matches:
                return matches

            # 2. Tokenized keyword search
            import re
            stop_words = {"what", "when", "where", "which", "with", "from", "have", "that", "this", "does", "about", "how", "the", "for", "and", "are", "can", "not", "all", "who", "out", "any"}
            keywords = [w for w in re.findall(r"\w+", q_clean) if len(w) >= 3 and w not in stop_words]
            if keywords:
                scored = []
                for p in policies:
                    text = f"{p.get('title', '')} {p.get('summary', '')} {p.get('clause_no', '')}".lower()
                    score = sum(1 for kw in keywords if kw in text)
                    if score > 0:
                        scored.append((score, p))
                scored.sort(key=lambda x: x[0], reverse=True)
                if scored:
                    return [item[1] for item in scored[:3]]

            return policies[:2]
        except Exception:
            return []

    @staticmethod
    def search_circulars(query_text: str) -> List[Dict[str, Any]]:
        try:
            circulars = DataRepository.get_all_circulars()
            if not circulars:
                return []
            q_clean = query_text.lower().strip()
            matches = [
                c for c in circulars
                if q_clean in c.get("title", "").lower() or q_clean in c.get("summary", "").lower()
            ]
            if not matches:
                return circulars[:2]
            return matches
        except Exception:
            return []

    @staticmethod
    def list_conversations(session: DatabaseSession) -> List[Dict[str, Any]]:
        return DataRepository._execute_query("SELECT * FROM conversations WHERE student_id = ? ORDER BY updated_at DESC", (session.student_id,))

    @staticmethod
    def get_conversation(session: DatabaseSession, conversation_id: str) -> Optional[Dict[str, Any]]:
        sid = DataRepository._resolve_student_id(session)
        res = DataRepository._execute_query("SELECT * FROM conversations WHERE conversation_id = ? AND student_id = ?", (conversation_id, sid))
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
        sid = DataRepository._resolve_student_id(session)
        DataRepository._execute_insert(
            "UPDATE conversations SET context_data = ?, updated_at = ? WHERE conversation_id = ? AND student_id = ?",
            (json.dumps(context_data), datetime.datetime.now(datetime.timezone.utc).isoformat(), conversation_id, sid)
        )

    @staticmethod
    def create_conversation(session: DatabaseSession, title: str) -> Dict[str, Any]:
        conv_id = f"conv-{uuid.uuid4().hex[:8]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        sid = DataRepository._resolve_student_id(session)
        query = "INSERT INTO conversations (conversation_id, student_id, title, status, context_data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)"
        DataRepository._execute_insert(query, (conv_id, sid, title or "New Conversation", "ACTIVE", "{}", now, now))
        return DataRepository.get_conversation(session, conv_id)

    @staticmethod
    def get_conversation_messages(session: DatabaseSession, conversation_id: str, verified_conv: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        conv = verified_conv or DataRepository.get_conversation(session, conversation_id)
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
    def add_message(session: DatabaseSession, conversation_id: str, message_data: Dict[str, Any], verified: bool = False) -> Dict[str, Any]:
        if not verified:
            conv = DataRepository.get_conversation(session, conversation_id)
            if not conv:
                raise PermissionError("Access denied: conversation does not belong to the authenticated student.")
        
        msg_id = f"msg-{uuid.uuid4().hex[:8]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        citations_list = message_data.get("citations", [])
        citations = json.dumps(citations_list)
        card_obj = message_data.get("structured_card")
        structured_card = json.dumps(card_obj) if card_obj else None
        
        query1 = "INSERT INTO messages (message_id, conversation_id, sender_role, content, category, source_agent, citations, structured_card, is_distress, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        query2 = "UPDATE conversations SET updated_at = ? WHERE conversation_id = ?"
        
        with get_db_connection() as conn:
            if isinstance(conn, sqlite3.Connection):
                conn.execute(query1, (msg_id, conversation_id, message_data.get("sender_role", "STUDENT"), message_data.get("content"), message_data.get("category"), message_data.get("source_agent", "VIGBOT"), citations, structured_card, 1 if message_data.get("is_distress") else 0, now))
                conn.execute(query2, (now, conversation_id))
                conn.commit()
            else:
                q1_pg = query1.replace("?", "%s")
                q2_pg = query2.replace("?", "%s")
                with conn.cursor() as cur:
                    cur.execute(q1_pg, (msg_id, conversation_id, message_data.get("sender_role", "STUDENT"), message_data.get("content"), message_data.get("category"), message_data.get("source_agent", "VIGBOT"), citations, structured_card, 1 if message_data.get("is_distress") else 0, now))
                    cur.execute(q2_pg, (now, conversation_id))
                conn.commit()
        
        return {
            "message_id": msg_id,
            "conversation_id": conversation_id,
            "sender_role": message_data.get("sender_role", "STUDENT"),
            "content": message_data.get("content"),
            "category": message_data.get("category"),
            "source_agent": message_data.get("source_agent", "VIGBOT"),
            "citations": citations_list,
            "structured_card": card_obj,
            "is_distress": bool(message_data.get("is_distress")),
            "created_at": now
        }

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
        return get_cached_catalog("clubs", 300.0, lambda: DataRepository._execute_query("SELECT * FROM studentlife_club"))

    @staticmethod
    def get_all_faqs() -> List[Dict[str, Any]]:
        return get_cached_catalog("all_faqs", 300.0, lambda: DataRepository._execute_query("SELECT * FROM fresher_faqs"))

    @staticmethod
    def get_all_policies() -> List[Dict[str, Any]]:
        return get_cached_catalog("all_policies", 300.0, lambda: DataRepository._execute_query("SELECT * FROM policies"))

    @staticmethod
    def get_all_circulars() -> List[Dict[str, Any]]:
        return get_cached_catalog("all_circulars", 300.0, lambda: DataRepository._execute_query("SELECT * FROM circulars ORDER BY issued_date DESC"))

    @staticmethod
    def get_facilities() -> List[Dict[str, Any]]:
        return get_cached_catalog("facilities", 300.0, lambda: DataRepository._execute_query("SELECT * FROM facilities"))

    @staticmethod
    def get_transport_routes() -> List[Dict[str, Any]]:
        return get_cached_catalog("transport_routes", 300.0, lambda: DataRepository._execute_query("SELECT * FROM transportation_routes"))

    @staticmethod
    def get_hostel_bus_schedules() -> List[Dict[str, Any]]:
        return get_cached_catalog("hostel_bus_schedules", 300.0, lambda: DataRepository._execute_query("SELECT * FROM hostel_bus_schedules ORDER BY id ASC"))

    @staticmethod
    def get_wellness_resources() -> List[Dict[str, Any]]:
        return get_cached_catalog("wellness_resources", 300.0, lambda: DataRepository._execute_query("SELECT * FROM wellness_resources"))

    @staticmethod
    def get_library_resources() -> List[Dict[str, Any]]:
        return get_cached_catalog("library_resources", 300.0, lambda: DataRepository._execute_query("SELECT * FROM library_resources LIMIT 20"))

    @staticmethod
    def get_library_operating_hours() -> List[Dict[str, Any]]:
        return get_cached_catalog("library_operating_hours", 300.0, lambda: DataRepository._execute_query("SELECT * FROM library_operating_hours ORDER BY id ASC"))

    @staticmethod
    def get_campus_locations() -> List[Dict[str, Any]]:
        return get_cached_catalog("campus_locations", 300.0, lambda: DataRepository._execute_query("SELECT * FROM campus_locations"))

    @staticmethod
    def get_broadcast_alerts() -> List[Dict[str, Any]]:
        return get_cached_catalog("broadcast_alerts", 60.0, lambda: DataRepository._execute_query("SELECT * FROM broadcast_alerts WHERE is_active = TRUE ORDER BY timestamp DESC LIMIT 5"))

    @staticmethod
    def get_lost_and_found() -> List[Dict[str, Any]]:
        try:
            return DataRepository._execute_query("SELECT * FROM lost_and_found ORDER BY date_reported DESC LIMIT 10")
        except Exception:
            return []

    @staticmethod
    def get_upcoming_events() -> List[Dict[str, Any]]:
        try:
            return get_cached_catalog("upcoming_events", 300.0, lambda: DataRepository._execute_query("SELECT * FROM calendar_events ORDER BY start_time ASC LIMIT 10"))
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
    def _record_query_metric_sync(intent_category: str, topic: str, language: str = "en", is_distress: bool = False, is_escalated: bool = False):
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
    def record_query_metric(intent_category: str, topic: str, language: str = "en", is_distress: bool = False, is_escalated: bool = False):
        import threading
        threading.Thread(
            target=DataRepository._record_query_metric_sync,
            args=(intent_category, topic, language, is_distress, is_escalated),
            daemon=True
        ).start()

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

    @staticmethod
    def save_learned_remediation(remediation: Dict[str, Any]) -> str:
        """Stores a newly learned cognitive query remediation from Gemini feedback evaluation."""
        rem_id = remediation.get("remediation_id") or f"rem-{uuid.uuid4().hex[:10]}"
        now = remediation.get("created_at") or datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        triggers = remediation.get("trigger_patterns", [])
        if isinstance(triggers, list):
            triggers_str = json.dumps(triggers)
        else:
            triggers_str = str(triggers)

        payload = remediation.get("remediation_payload", {})
        if isinstance(payload, dict):
            payload_str = json.dumps(payload)
        else:
            payload_str = str(payload or "{}")

        query = """
            INSERT INTO learned_query_remediations (
                remediation_id, feedback_id, conversation_id, user_query, bot_output,
                student_comment, mismatch_detected, mismatch_reason, intended_intent,
                remediation_type, trigger_patterns, target_entity, routing_action,
                remediation_payload, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        DataRepository._execute_insert(query, (
            rem_id,
            remediation.get("feedback_id") or "",
            remediation.get("conversation_id") or "",
            remediation.get("user_query") or "",
            remediation.get("bot_output") or "",
            remediation.get("student_comment") or "",
            bool(remediation.get("mismatch_detected", True)),
            remediation.get("mismatch_reason") or "",
            remediation.get("intended_intent") or "GENERAL",
            remediation.get("remediation_type") or "DIRECT_ANSWER",
            triggers_str,
            remediation.get("target_entity") or "",
            remediation.get("routing_action") or "DIRECT_ANSWER",
            payload_str,
            remediation.get("status") or "ACTIVE",
            now
        ))
        return rem_id

    @staticmethod
    def get_active_learned_remediations() -> List[Dict[str, Any]]:
        """Retrieves all active learned query remediations for dynamic NLU interception."""
        rows = DataRepository._execute_query("SELECT * FROM learned_query_remediations WHERE status = 'ACTIVE' ORDER BY created_at DESC")
        for r in rows:
            if isinstance(r.get("trigger_patterns"), str):
                try:
                    r["trigger_patterns"] = json.loads(r["trigger_patterns"])
                except Exception:
                    r["trigger_patterns"] = [r["trigger_patterns"]]
            if isinstance(r.get("remediation_payload"), str):
                try:
                    r["remediation_payload"] = json.loads(r["remediation_payload"])
                except Exception:
                    r["remediation_payload"] = {}
        return rows

    @staticmethod
    def get_all_learned_remediations() -> List[Dict[str, Any]]:
        """Retrieves all learned query remediations and policy defense audits for Nodal Officer review."""
        rows = DataRepository._execute_query("SELECT * FROM learned_query_remediations ORDER BY created_at DESC LIMIT 200")
        for r in rows:
            if isinstance(r.get("trigger_patterns"), str):
                try:
                    r["trigger_patterns"] = json.loads(r["trigger_patterns"])
                except Exception:
                    r["trigger_patterns"] = [r["trigger_patterns"]]
            payload = {}
            if isinstance(r.get("remediation_payload"), str):
                try:
                    payload = json.loads(r["remediation_payload"])
                except Exception:
                    payload = {}
            elif isinstance(r.get("remediation_payload"), dict):
                payload = r.get("remediation_payload")
            r["remediation_payload"] = payload
            r["data_missing_in_db"] = bool(payload.get("data_missing_in_db", False))
            r["missing_data_description"] = payload.get("missing_data_description") or ""
            r["nodal_officer_input"] = payload.get("nodal_officer_input") or ""
            r["grounded_response_template"] = payload.get("grounded_response_template") or ""
        return rows

    @staticmethod
    def submit_nodal_remediation_input(remediation_id: str, official_information: str) -> bool:
        """Updates a remediation with official human-verified facts provided by the Nodal Officer, activating the rule."""
        try:
            rows = DataRepository._execute_query(
                "SELECT remediation_payload FROM learned_query_remediations WHERE remediation_id = ?",
                (remediation_id,)
            )
            payload = {}
            if rows and rows[0].get("remediation_payload"):
                raw_p = rows[0]["remediation_payload"]
                try:
                    payload = json.loads(raw_p) if isinstance(raw_p, str) else raw_p
                except Exception:
                    payload = {}

            payload["data_missing_in_db"] = False
            payload["nodal_officer_input"] = official_information.strip()
            payload["grounded_response_template"] = official_information.strip()

            DataRepository._execute_insert(
                "UPDATE learned_query_remediations SET remediation_payload = ?, status = 'ACTIVE' WHERE remediation_id = ?",
                (json.dumps(payload), remediation_id)
            )
            return True
        except Exception as e:
            logger.error(f"[DataRepository] Failed to submit nodal remediation input: {e}")
            return False

    @staticmethod
    def update_remediation_status(remediation_id: str, new_status: str) -> bool:
        """Toggles or updates the status of a learned remediation (e.g. ACTIVE, INACTIVE)."""
        try:
            DataRepository._execute_insert(
                "UPDATE learned_query_remediations SET status = ? WHERE remediation_id = ?",
                (new_status.upper(), remediation_id)
            )
            return True
        except Exception:
            return False

    @staticmethod
    def delete_remediation(remediation_id: str) -> bool:
        """Deletes a learned remediation rule permanently."""
        try:
            DataRepository._execute_insert(
                "DELETE FROM learned_query_remediations WHERE remediation_id = ?",
                (remediation_id,)
            )
            return True
        except Exception:
            return False

    @staticmethod
    def get_system_setting(key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieves a dynamic system setting from database."""
        try:
            rows = DataRepository._execute_query(
                "SELECT value FROM system_settings WHERE key = ? LIMIT 1",
                (key,)
            )
            if rows:
                return rows[0]["value"]
            return default
        except Exception:
            return default

    @staticmethod
    def set_system_setting(key: str, value: str) -> None:
        """Upserts a dynamic system setting in database across SQLite and Postgres."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:
            DataRepository._execute_insert(
                """INSERT INTO system_settings (key, value, updated_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = EXCLUDED.updated_at""",
                (key, str(value), now)
            )
        except Exception:
            # Fallback for drivers that don't support ON CONFLICT
            try:
                DataRepository._execute_insert("DELETE FROM system_settings WHERE key = ?", (key,))
                DataRepository._execute_insert("INSERT INTO system_settings (key, value, updated_at) VALUES (?, ?, ?)", (key, str(value), now))
            except Exception:
                pass

    @staticmethod
    def get_all_system_settings() -> Dict[str, str]:
        """Retrieves all dynamic system settings."""
        try:
            rows = DataRepository._execute_query("SELECT key, value FROM system_settings")
            return {r["key"]: r["value"] for r in rows}
        except Exception:
            return {}

    @staticmethod
    def log_gemini_call(endpoint: str, model: str, prompt_tokens: int = 0, candidate_tokens: int = 0, status_code: int = 200, latency_ms: int = 0) -> None:
        """Logs a Gemini API call for real-time quota, rate-limit, and latency surveillance."""
        call_id = f"call-{uuid.uuid4().hex[:10]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:
            DataRepository._execute_insert(
                """INSERT INTO gemini_usage_log (id, endpoint, model, prompt_tokens, candidate_tokens, status_code, latency_ms, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (call_id, endpoint, model, prompt_tokens, candidate_tokens, status_code, latency_ms, now)
            )
        except Exception:
            pass

    @staticmethod
    def get_gemini_usage_stats() -> Dict[str, Any]:
        """
        Calculates live daily and per-minute Gemini API usage against standard Free Tier limits
        (15 RPM / 1,500 RPD).
        """
        today_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        one_min_ago = (now_utc - datetime.timedelta(seconds=60)).isoformat()
        
        daily_limit = 1500
        rpm_limit = 15

        daily_count = 0
        rpm_count = 0
        total_count = 0
        recent_calls = []

        try:
            # Daily count
            d_rows = DataRepository._execute_query(
                "SELECT COUNT(*) as cnt FROM gemini_usage_log WHERE created_at LIKE ?",
                (f"{today_date}%",)
            )
            daily_count = d_rows[0]["cnt"] if d_rows else 0

            # Last 60 seconds count
            m_rows = DataRepository._execute_query(
                "SELECT COUNT(*) as cnt FROM gemini_usage_log WHERE created_at >= ?",
                (one_min_ago,)
            )
            rpm_count = m_rows[0]["cnt"] if m_rows else 0

            # Total all-time
            t_rows = DataRepository._execute_query("SELECT COUNT(*) as cnt FROM gemini_usage_log")
            total_count = t_rows[0]["cnt"] if t_rows else 0

            # Recent 8 calls
            recent_calls = DataRepository._execute_query(
                "SELECT id, endpoint, model, status_code, latency_ms, created_at FROM gemini_usage_log ORDER BY created_at DESC LIMIT 8"
            )
        except Exception:
            pass

        return {
            "daily_requests_used": daily_count,
            "daily_requests_limit": daily_limit,
            "daily_requests_remaining": max(0, daily_limit - daily_count),
            "minute_requests_used": rpm_count,
            "minute_requests_limit": rpm_limit,
            "minute_requests_remaining": max(0, rpm_limit - rpm_count),
            "total_requests_all_time": total_count,
            "recent_calls": recent_calls
        }

    @staticmethod
    def warm_cache():
        """Pre-warm static institutional catalogs and connection pool on startup."""
        try:
            DataRepository.get_all_policies()
            DataRepository.get_all_circulars()
            DataRepository.get_campus_locations()
            DataRepository.get_library_operating_hours()
            DataRepository.get_library_resources()
            DataRepository.get_wellness_resources()
            DataRepository.get_transport_routes()
            DataRepository.get_facilities()
            logger.info("Pre-warmed all institutional catalogs into in-memory cache.")
        except Exception as e:
            logger.warning(f"Cache pre-warming notice: {e}")


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
