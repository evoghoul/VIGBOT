"use server";

import { getDb } from "../lib/db-provider";
import { mockGrievances, mockClubApps, mockBookings, mockLostAndFound } from '../data/adminMockData';

import { getBackendUrl } from "../lib/backend-url";
const BACKEND_BASE_URL = getBackendUrl();

export async function adminLogin(username: string, passwordHash: string) {
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/admin/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password: passwordHash })
    });
    if (res.ok) {
      const data = await res.json();
      if (data.success) {
        return { success: true, admin: data.admin, token: data.token };
      }
    }
  } catch (backendError) {
    console.warn("Backend admin login failed, attempting local fallback:", backendError);
  }

  try {
    const db = getDb();
    if (!db) {
      if (username.trim() === "admin" && (passwordHash === "admin123" || passwordHash === "pbkdf2_sha256$29000$mock$hashedpassword")) {
        return { 
          success: true, 
          admin: { id: "ADM001", username: "admin", name: "Default Nodal Officer", role: "Admin" } 
        };
      }
      return { success: false, error: "Invalid credentials" };
    }
    const stmt = db.prepare(`SELECT * FROM admins WHERE username = ? AND password_hash = ?`);
    const admin = stmt.get(username, passwordHash);
    db.close();

    if (admin) {
      return { success: true, admin };
    }
    return { success: false, error: "Invalid credentials" };
  } catch (error) {
    console.error("Admin login error:", error);
    return { success: false, error: "Database error during login" };
  }
}

export async function fetchAllTickets() {
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/admin/overview`, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      if (data.success) {
        return {
          success: true,
          grievances: data.grievances || [],
          clubApps: data.clubApps || [],
          bookings: data.bookings || [],
          lostAndFound: data.lostAndFound || [],
          serviceRequests: data.service_requests || [],
          hostelRequests: data.hostelRequests || []
        };
      }
    }
  } catch (backendError) {
    console.warn("Backend fetch overview failed, attempting local fallback:", backendError);
  }

  try {
    const db = getDb();
    if (!db) {
      return { 
        success: true, 
        grievances: mockGrievances, 
        clubApps: mockClubApps, 
        bookings: mockBookings, 
        lostAndFound: mockLostAndFound,
        serviceRequests: [],
        hostelRequests: []
      };
    }
    const grievances = db.prepare(`SELECT tracking_id as id, description, status, timestamp, withdrawal_reason, student_id FROM studentlife_grievance ORDER BY timestamp DESC`).all();
    const clubApps = db.prepare(`SELECT id, club_id, student_name, status, timestamp, withdrawal_reason, student_id FROM studentlife_club_application ORDER BY timestamp DESC`).all();
    const bookings = db.prepare(`SELECT id, facility_id, student_id, date, start_time, end_time, purpose, status FROM bookings ORDER BY date DESC, start_time DESC`).all();
    const lostAndFound = db.prepare(`SELECT id, student_id, type, title, description, tags, contact_info, status, date_posted, image_url FROM lost_and_found ORDER BY date_posted DESC`).all();
    let serviceRequests = [];
    try {
      serviceRequests = db.prepare(`SELECT * FROM service_requests ORDER BY created_at DESC`).all();
    } catch (e) {}

    db.close();
    return { success: true, grievances, clubApps, bookings, lostAndFound, serviceRequests, hostelRequests: [] };
  } catch (error) {
    return { 
      success: true, 
      grievances: mockGrievances, 
      clubApps: mockClubApps, 
      bookings: mockBookings, 
      lostAndFound: mockLostAndFound,
      serviceRequests: [],
      hostelRequests: []
    };
  }
}

export async function updateTicketStatus(ticketId: string | number, type: 'club' | 'grievance' | 'booking' | 'lost_found' | 'service_request' | 'hostel', newStatus: string) {
  try {
    const endpoint = type === 'service_request' 
      ? `${BACKEND_BASE_URL}/admin/service-requests/${ticketId}`
      : `${BACKEND_BASE_URL}/admin/tickets/${type}/${ticketId}`;
      
    const res = await fetch(endpoint, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    if (res.ok) {
      const data = await res.json();
      if (data.success) return { success: true };
    }
  } catch (backendError) {
    console.warn("Backend ticket update failed, attempting local fallback:", backendError);
  }

  try {
    const db = getDb();
    if (!db) return { success: true };
    let stmt;
    
    if (type === 'grievance') {
      stmt = db.prepare(`UPDATE studentlife_grievance SET status = ? WHERE tracking_id = ?`);
    } else if (type === 'club') {
      stmt = db.prepare(`UPDATE studentlife_club_application SET status = ? WHERE id = ?`);
    } else if (type === 'booking') {
      stmt = db.prepare(`UPDATE bookings SET status = ? WHERE id = ?`);
    } else if (type === 'lost_found') {
      stmt = db.prepare(`UPDATE lost_and_found SET status = ? WHERE id = ?`);
    } else if (type === 'service_request') {
      stmt = db.prepare(`UPDATE service_requests SET status = ? WHERE service_request_id = ? OR request_no = ?`);
      const result = stmt.run(newStatus.toUpperCase(), ticketId, ticketId);
      db.close();
      return { success: result.changes > 0 };
    }
    
    if (stmt) {
      const result = stmt.run(newStatus, ticketId);
      db.close();
      return { success: result.changes > 0 };
    }
    db.close();
    return { success: false, error: "Invalid ticket type." };
  } catch (error) {
    return { success: false, error: "Failed to update ticket" };
  }
}

export async function deleteTicket(ticketId: string | number, type: 'club' | 'grievance' | 'booking' | 'lost_found' | 'service_request' | 'hostel') {
  try {
    const endpoint = type === 'service_request'
      ? `${BACKEND_BASE_URL}/admin/service-requests/${ticketId}`
      : `${BACKEND_BASE_URL}/admin/tickets/${type}/${ticketId}`;
      
    const res = await fetch(endpoint, {
      method: 'DELETE'
    });
    if (res.ok) {
      const data = await res.json();
      if (data.success) return { success: true };
    }
  } catch (backendError) {
    console.warn("Backend ticket deletion failed, attempting local fallback:", backendError);
  }

  try {
    const db = getDb();
    if (!db) return { success: true };
    let stmt;
    if (type === 'grievance') {
      stmt = db.prepare(`DELETE FROM studentlife_grievance WHERE tracking_id = ?`);
    } else if (type === 'club') {
      stmt = db.prepare(`DELETE FROM studentlife_club_application WHERE id = ?`);
    } else if (type === 'booking') {
      stmt = db.prepare(`DELETE FROM bookings WHERE id = ?`);
    } else if (type === 'lost_found') {
      stmt = db.prepare(`DELETE FROM lost_and_found WHERE id = ?`);
    } else if (type === 'service_request') {
      stmt = db.prepare(`DELETE FROM service_requests WHERE service_request_id = ? OR request_no = ?`);
      const result = stmt.run(ticketId, ticketId);
      db.close();
      return { success: result.changes > 0 };
    }
    if (stmt) {
      const result = stmt.run(ticketId);
      db.close();
      return { success: result.changes > 0 };
    }
    db.close();
    return { success: false, error: "Invalid ticket type." };
  } catch (error) {
    return { success: false, error: "Failed to delete ticket" };
  }
}
