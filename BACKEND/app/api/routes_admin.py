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
