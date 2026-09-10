import { NextRequest, NextResponse } from "next/server";
import { clientIp } from "@/lib/clientIp";

// Proxies straight through to the FastAPI backend's /api/open-pr — same
// server-to-server pattern as every other route in app/api/backend/*
// (see analyze-repo/route.ts). The request body carries a GitHub PAT:
// this route reads it only as opaque bytes to forward, never parses,
// logs, or persists it — Next.js's own request logging in dev/prod does
// not log bodies, and nothing here adds any.
export const maxDuration = 30;

export async function POST(request: NextRequest) {
  const backendUrl = process.env.KAGUTSUCHI_API_URL;
  if (!backendUrl) {
    return NextResponse.json({ detail: "Backend not configured" }, { status: 503 });
  }

  const bodyText = await request.text();

  try {
    const upstream = await fetch(`${backendUrl.replace(/\/$/, "")}/api/open-pr`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Client-IP": clientIp(request) },
      body: bodyText,
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
