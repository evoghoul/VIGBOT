"use server";

import { getDb } from "../lib/db-provider";

const BACKEND_BASE_URL = (process.env.NEXT_PUBLIC_BACKEND_URL || "https://vigbot-api.onrender.com/api/v1").replace(/\/+$/, "");

export async function getWellnessResources() {
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/community/wellness`, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      if (data.success && Array.isArray(data.resources)) {
        return data.resources;
      }
    }
  } catch (backendError) {
    console.warn("Backend fetch failed for wellness resources:", backendError);
  }

  try {
    const db = getDb();
    if (!db) return [];
    const rows = db.prepare("SELECT * FROM wellness_resources").all();
    db.close();
    return rows;
  } catch (error) {
    console.error("Error fetching wellness resources:", error);
    return [];
  }
}
