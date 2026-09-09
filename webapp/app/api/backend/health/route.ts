import { NextResponse } from "next/server";

// Lightweight, no rate limit, no persistence -- just answers "is the
// backend reachable right now" so the UI can tell a visitor honestly
// instead of letting them discover it via a confusing error after they
// submit a scan.
export async function GET() {
  const backendUrl = process.env.KAGUTSUCHI_API_URL;
  if (!backendUrl) {
    return NextResponse.json({ online: false, detail: "Backend not configured" });
  }
  try {
    const upstream = await fetch(`${backendUrl.replace(/\/$/, "")}/api/health`, {
      signal: AbortSignal.timeout(5000),
    });
    return NextResponse.json({ online: upstream.ok });
  } catch {
    return NextResponse.json({ online: false, detail: "Backend unreachable" });
  }
}
