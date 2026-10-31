"use server";

import { getDb } from "../lib/db-provider";

const BACKEND_BASE_URL = (process.env.NEXT_PUBLIC_BACKEND_URL || "https://vigbot-api.onrender.com/api/v1").replace(/\/+$/, "");

export async function getTransportRoutes() {
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/community/transport`, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      if (data.success && Array.isArray(data.routes)) {
        return data.routes;
      }
    }
  } catch (backendError) {
    console.warn("Backend fetch failed for transport:", backendError);
  }

  try {
    const db = getDb();
    if (!db) return [];
    const rows = db.prepare("SELECT * FROM transportation_routes").all();
    db.close();
    return rows;
  } catch (error) {
    console.error("Error fetching transport routes:", error);
    return [];
  }
}
