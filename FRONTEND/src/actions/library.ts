"use server";

import { getDb } from "../lib/db-provider";

const BACKEND_BASE_URL = (process.env.NEXT_PUBLIC_BACKEND_URL || "https://vigbot-api.onrender.com/api/v1").replace(/\/+$/, "");

export async function getLibraryResources() {
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/community/library`, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      if (data.success && Array.isArray(data.resources)) {
        return data.resources;
      }
    }
  } catch (backendError) {
    console.warn("Backend fetch failed for library resources:", backendError);
  }

  try {
    const db = getDb();
    if (!db) return [];
    const rows = db.prepare("SELECT * FROM library_resources ORDER BY id DESC").all();
    db.close();
    return rows;
  } catch (error) {
    console.error("Error fetching library resources:", error);
    return [];
  }
}
