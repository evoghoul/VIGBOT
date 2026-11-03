import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from app.database import DataRepository, get_db_connection

router = APIRouter(prefix="/admin", tags=["Nodal Office & Administration"])


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class StatusUpdateRequest(BaseModel):
    status: str
    remarks: Optional[str] = None


class ServiceRequestAdminCreate(BaseModel):
    student_id: str
    category: str
    title: str
    description: str
    priority: Optional[str] = "NORMAL"
    status: Optional[str] = "SUBMITTED"


# -------------------------------------------------------------
# 1. Nodal Officer Login
# -------------------------------------------------------------
@router.post("/login")
async def admin_login(req: AdminLoginRequest):
    try:
        admins = DataRepository._execute_query(
            "SELECT id, username, name, role FROM admins WHERE username = ? AND password_hash = ?",
            (req.username.strip(), req.password.strip())
        )
        if admins:
            return {
                "success": True,
                "token": f"nodal-token-{admins[0]['id']}",
                "admin": admins[0]
            }
        # Fallback for default credential check
        if req.username.strip() == "admin" and req.password.strip() == "admin123":
            return {
                "success": True,
                "token": "nodal-token-ADM001",
                "admin": {
                    "id": "ADM001",
                    "username": "admin",
                    "name": "Nodal Officer",
                    "role": "Chief Nodal Officer"
                }
            }
        return {"success": False, "error": "Invalid administrative credentials."}
    except Exception as e:
        return {"success": False, "error": f"Database error: {str(e)}"}


# -------------------------------------------------------------
# 2. Complete Services & Requests Overview for Nodal Office
# -------------------------------------------------------------
@router.get("/overview")
async def get_services_overview():
    """
    Returns live university service requests, grievances, club apps,
    facility bookings, lost & found, and hostel requests directly from Neon PostgreSQL.
    """
    try:
        service_requests = DataRepository._execute_query(
            "SELECT * FROM service_requests ORDER BY created_at DESC LIMIT 100"
        )
        grievances = DataRepository._execute_query(
            "SELECT tracking_id as id, description, status, timestamp, withdrawal_reason, student_id FROM studentlife_grievance ORDER BY timestamp DESC LIMIT 100"
        )
        club_apps = DataRepository._execute_query(
            "SELECT id, club_id, student_name, status, timestamp, withdrawal_reason, student_id FROM studentlife_club_application ORDER BY timestamp DESC LIMIT 100"
        )
        bookings = DataRepository._execute_query(
            "SELECT id, facility_id, student_id, date, start_time, end_time, purpose, status FROM bookings ORDER BY date DESC, start_time DESC LIMIT 100"
        )
        lost_and_found = DataRepository._execute_query(
            "SELECT id, student_id, type, title, description, tags, contact_info, status, date_posted, image_url FROM lost_and_found ORDER BY date_posted DESC LIMIT 100"
        )
        hostel_requests = DataRepository._execute_query(
            "SELECT id, student_id, type, details, status, created_at FROM hostel_requests ORDER BY created_at DESC LIMIT 100"
        )

        return {
            "success": True,
            "counts": {
                "service_requests": len(service_requests),
                "grievances": len(grievances),
                "club_applications": len(club_apps),
                "bookings": len(bookings),
                "lost_and_found": len(lost_and_found),
                "hostel_requests": len(hostel_requests),
            },
            "service_requests": service_requests,
            "grievances": grievances,
            "clubApps": club_apps,
            "bookings": bookings,
            "lostAndFound": lost_and_found,
            "hostelRequests": hostel_requests
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to fetch overview: {str(e)}"}


# -------------------------------------------------------------
# 3. Update Status of Any Service Request
# -------------------------------------------------------------
@router.patch("/service-requests/{request_id}")
async def update_service_request_status(request_id: str, req: StatusUpdateRequest):
    try:
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        DataRepository._execute_insert(
            "UPDATE service_requests SET status = ?, updated_at = ? WHERE service_request_id = ? OR request_no = ?",
            (req.status.upper(), now_iso, request_id, request_id)
        )
        return {
            "success": True,
            "message": f"Service request {request_id} updated to {req.status.upper()}."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to update service request: {str(e)}"}


# -------------------------------------------------------------
# 4. Delete Any Service Request (Permanent Deletion)
# -------------------------------------------------------------
@router.delete("/service-requests/{request_id}")
async def delete_service_request(request_id: str):
    try:
        DataRepository._execute_insert(
            "DELETE FROM service_requests WHERE service_request_id = ? OR request_no = ?",
            (request_id, request_id)
        )
        return {
            "success": True,
            "message": f"Service request {request_id} deleted successfully."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to delete service request: {str(e)}"}


# -------------------------------------------------------------
# 5. Generic Ticket Status Update (Grievance, Club, Booking, Lost & Found, Hostel)
# -------------------------------------------------------------
@router.patch("/tickets/{ticket_type}/{ticket_id}")
async def update_generic_ticket_status(ticket_type: str, ticket_id: str, req: StatusUpdateRequest):
    try:
        tt = ticket_type.lower()
        if tt == "grievance":
            DataRepository._execute_insert(
                "UPDATE studentlife_grievance SET status = ? WHERE tracking_id = ?",
                (req.status, ticket_id)
            )
        elif tt == "club":
            DataRepository._execute_insert(
                "UPDATE studentlife_club_application SET status = ? WHERE id = ?",
                (req.status, int(ticket_id))
            )
        elif tt == "booking":
            DataRepository._execute_insert(
                "UPDATE bookings SET status = ? WHERE id = ?",
                (req.status.lower(), int(ticket_id))
            )
        elif tt in ("lost_found", "lostandfound", "lost"):
            DataRepository._execute_insert(
                "UPDATE lost_and_found SET status = ? WHERE id = ?",
                (req.status.lower(), int(ticket_id))
            )
        elif tt == "hostel":
            DataRepository._execute_insert(
                "UPDATE hostel_requests SET status = ? WHERE id = ?",
                (req.status, int(ticket_id))
            )
        else:
            return {"success": False, "error": f"Unsupported ticket type: {ticket_type}"}

        return {
            "success": True,
            "message": f"{ticket_type.capitalize()} {ticket_id} status updated to {req.status}."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to update ticket: {str(e)}"}


# -------------------------------------------------------------
# 6. Generic Ticket Deletion (Grievance, Club, Booking, Lost & Found, Hostel)
# -------------------------------------------------------------
@router.delete("/tickets/{ticket_type}/{ticket_id}")
async def delete_generic_ticket(ticket_type: str, ticket_id: str):
    try:
        tt = ticket_type.lower()
        if tt == "grievance":
            DataRepository._execute_insert(
                "DELETE FROM studentlife_grievance WHERE tracking_id = ?",
                (ticket_id,)
            )
        elif tt == "club":
            DataRepository._execute_insert(
                "DELETE FROM studentlife_club_application WHERE id = ?",
                (int(ticket_id),)
            )
        elif tt == "booking":
            DataRepository._execute_insert(
                "DELETE FROM bookings WHERE id = ?",
                (int(ticket_id),)
            )
        elif tt in ("lost_found", "lostandfound", "lost"):
            DataRepository._execute_insert(
                "DELETE FROM lost_and_found WHERE id = ?",
                (int(ticket_id),)
            )
        elif tt == "hostel":
            DataRepository._execute_insert(
                "DELETE FROM hostel_requests WHERE id = ?",
                (int(ticket_id),)
            )
        elif tt == "service_request":
            DataRepository._execute_insert(
                "DELETE FROM service_requests WHERE service_request_id = ? OR request_no = ?",
                (ticket_id, ticket_id)
            )
        else:
            return {"success": False, "error": f"Unsupported ticket type: {ticket_type}"}

        return {
            "success": True,
            "message": f"{ticket_type.capitalize()} {ticket_id} deleted permanently."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to delete ticket: {str(e)}"}



# -------------------------------------------------------------
# 7. Cognitive Remediations & Disliked Query Audits (Nodal Surveillance)
# -------------------------------------------------------------
class RemediationStatusRequest(BaseModel):
    status: str


class GeminiConfigRequest(BaseModel):
    api_key: Optional[str] = None
    enable_gemini: Optional[bool] = None
    model: Optional[str] = None


@router.get("/remediations")
async def get_cognitive_remediations():
    """
    Retrieves all disliked queries, Gemini audit diagnoses, and instructed
    remediation rules pushed to Neon DB for Nodal Officer surveillance.
    """
    try:
        remediations = DataRepository.get_all_learned_remediations()
        feedback_rows = DataRepository._execute_query("SELECT * FROM message_feedback ORDER BY created_at DESC LIMIT 100")
        
        active_count = sum(1 for r in remediations if r.get("status") == "ACTIVE")
        policy_count = sum(1 for r in remediations if r.get("status") == "POLICY_PROTECTED")
        inactive_count = sum(1 for r in remediations if r.get("status") == "INACTIVE")

        return {
            "success": True,
            "summary": {
                "total_audited": len(remediations),
                "active_rules": active_count,
                "policy_protected": policy_count,
                "inactive_rules": inactive_count,
                "raw_feedback_count": len(feedback_rows)
            },
            "remediations": remediations,
            "recent_feedback": feedback_rows
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to fetch remediations: {str(e)}"}


@router.patch("/remediations/{remediation_id}/status")
async def update_remediation_status(remediation_id: str, req: RemediationStatusRequest):
    """Toggles a learned remediation between ACTIVE and INACTIVE."""
    try:
        success = DataRepository.update_remediation_status(remediation_id, req.status)
        from app.agent.feedback_remediator import FeedbackRemediationService
        FeedbackRemediationService._cache_active_remediations = None
        return {
            "success": success,
            "remediation_id": remediation_id,
            "status": req.status.upper(),
            "message": f"Remediation status updated to {req.status.upper()}."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to update remediation status: {str(e)}"}


@router.delete("/remediations/{remediation_id}")
async def delete_remediation_rule(remediation_id: str):
    """Deletes a learned remediation rule permanently from Neon DB."""
    try:
        success = DataRepository.delete_remediation(remediation_id)
        from app.agent.feedback_remediator import FeedbackRemediationService
        FeedbackRemediationService._cache_active_remediations = None
        return {
            "success": success,
            "remediation_id": remediation_id,
            "message": f"Remediation rule {remediation_id} permanently removed."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to delete remediation rule: {str(e)}"}


# -------------------------------------------------------------
# 8. Gemini API Quota, Live Telemetry & Dynamic Key Switcher
# -------------------------------------------------------------
@router.get("/gemini/status")
async def get_gemini_status():
    """
    Returns live Gemini API operational status, key masking, model details,
    and remaining Free Tier quota (15 RPM / 1,500 RPD).
    """
    try:
        from app.config import settings
        from app.agent.feedback_remediator import FeedbackRemediationService

        key = FeedbackRemediationService.get_gemini_api_key()
        enabled = getattr(settings, "ENABLE_GEMINI", False)
        stored_enabled = DataRepository.get_system_setting("ENABLE_GEMINI")
        if stored_enabled is not None:
            enabled = stored_enabled.lower() in ("true", "1", "yes")

        model = DataRepository.get_system_setting("GEMINI_MODEL") or getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")

        masked_key = ""
        if key:
            if len(key) > 12:
                masked_key = f"{key[:8]}{'*' * 24}{key[-4:]}"
            else:
                masked_key = "********"

        usage = DataRepository.get_gemini_usage_stats()

        return {
            "success": True,
            "enable_gemini": enabled,
            "masked_api_key": masked_key,
            "has_key": bool(key),
            "active_model": model,
            "available_models": [
                "gemini-2.5-flash",
                "gemini-2.5-pro",
                "gemini-2.0-flash",
                "gemini-1.5-flash",
                "gemini-3.5-flash"
            ],
            "quota": usage
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to fetch Gemini status: {str(e)}"}


@router.post("/gemini/config")
async def update_gemini_config(req: GeminiConfigRequest):
    """
    Switches or updates the Gemini API key, active model, or enablement status.
    Strictly verifies the key against Google Gemini API before saving to Neon DB.
    """
    import urllib.request
    import urllib.error
    import time
    from app.config import settings
    import os

    try:
        t0 = time.time()

        # If a new API key was submitted, test and validate with Google first
        if req.api_key is not None:
            clean_key = req.api_key.strip()
            if clean_key:
                test_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={clean_key}"
                try:
                    req_obj = urllib.request.Request(test_url, headers={"User-Agent": "VIGBOT-Admin/1.0"})
                    with urllib.request.urlopen(req_obj, timeout=12) as resp:
                        latency = int((time.time() - t0) * 1000)
                        DataRepository.log_gemini_call(
                            endpoint="key_verification",
                            model="models_list",
                            status_code=200,
                            latency_ms=latency
                        )
                except urllib.error.HTTPError as he:
                    latency = int((time.time() - t0) * 1000)
                    DataRepository.log_gemini_call(
                        endpoint="key_verification",
                        model="models_list",
                        status_code=he.code,
                        latency_ms=latency
                    )
                    if he.code in (400, 403):
                        return {
                            "success": False,
                            "error": f"Authentication Failed (HTTP {he.code}): The provided Gemini API Key is invalid or rejected by Google."
                        }
                    elif he.code == 429:
                        return {
                            "success": False,
                            "error": "Rate Limit Exceeded (HTTP 429): Google reports quota exhausted for this API key."
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Google Gemini API error: {he.reason} (HTTP {he.code})"
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Unable to reach Google Gemini API: {str(e)}"
                    }

                # Persist validated key in Neon DB system_settings
                DataRepository.set_system_setting("GEMINI_API_KEY", clean_key)
                settings.GEMINI_API_KEY = clean_key
                os.environ["GEMINI_API_KEY"] = clean_key

        if req.enable_gemini is not None:
            DataRepository.set_system_setting("ENABLE_GEMINI", "true" if req.enable_gemini else "false")
            settings.ENABLE_GEMINI = req.enable_gemini

        if req.model is not None and req.model.strip():
            clean_model = req.model.strip()
            DataRepository.set_system_setting("GEMINI_MODEL", clean_model)
            settings.GEMINI_MODEL = clean_model

        # Update local .env if writable
        try:
            env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                new_lines = []
                for l in lines:
                    if req.api_key and l.startswith("GEMINI_API_KEY="):
                        new_lines.append(f"GEMINI_API_KEY={req.api_key.strip()}\n")
                    elif req.enable_gemini is not None and l.startswith("ENABLE_GEMINI="):
                        new_lines.append(f"ENABLE_GEMINI={'true' if req.enable_gemini else 'false'}\n")
                    elif req.model and l.startswith("GEMINI_MODEL="):
                        new_lines.append(f"GEMINI_MODEL={req.model.strip()}\n")
                    else:
                        new_lines.append(l)
                with open(env_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
        except Exception:
            pass

        return {
            "success": True,
            "message": "Gemini configuration verified and updated successfully.",
            "enable_gemini": getattr(settings, "ENABLE_GEMINI", False),
            "active_model": getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
        }
    except Exception as e:
        return {"success": False, "error": f"Configuration update failed: {str(e)}"}


@router.post("/gemini/ping")
async def ping_gemini_connection():
    """Pings Google Gemini API to test current key latency and quota health."""
    import urllib.request
    import urllib.error
    import time
    from app.agent.feedback_remediator import FeedbackRemediationService

    key = FeedbackRemediationService.get_gemini_api_key()
    if not key:
        return {
            "success": False,
            "error": "No Gemini API Key is configured. Please enter and save an API key."
        }

    t0 = time.time()
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    try:
        req_obj = urllib.request.Request(url, headers={"User-Agent": "VIGBOT-Admin/1.0"})
        with urllib.request.urlopen(req_obj, timeout=10) as resp:
            latency = int((time.time() - t0) * 1000)
            DataRepository.log_gemini_call(
                endpoint="ping",
                model="models_list",
                status_code=200,
                latency_ms=latency
            )
            return {
                "success": True,
                "status": "Operational",
                "status_code": 200,
                "latency_ms": latency,
                "message": f"Successfully connected to Google Gemini API in {latency}ms."
            }
    except urllib.error.HTTPError as he:
        latency = int((time.time() - t0) * 1000)
        DataRepository.log_gemini_call(endpoint="ping", model="models_list", status_code=he.code, latency_ms=latency)
        return {
            "success": False,
            "status_code": he.code,
            "latency_ms": latency,
            "error": f"Gemini API returned HTTP {he.code}: {he.reason}"
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to reach Gemini: {str(e)}"}
