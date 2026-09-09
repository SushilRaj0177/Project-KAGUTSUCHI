import { NextRequest, NextResponse } from "next/server";

// See app/api/backend/analyze-repo/route.ts for why this proxy exists.
export const maxDuration = 60;

export async function POST(request: NextRequest) {
  const backendUrl = process.env.KAGUTSUCHI_API_URL;
  if (!backendUrl) {
    return NextResponse.json({ detail: "Backend not configured" }, { status: 503 });
  }

  const body = await request.text();
  try {
    const upstream = await fetch(`${backendUrl.replace(/\/$/, "")}/api/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
    });
    const data = await upstream.text();
    return new NextResponse(data, {
      status: upstream.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    return NextResponse.json(
      { detail: `Could not reach backend: ${err instanceof Error ? err.message : String(err)}` },
      { status: 502 },
    );
  }
}
