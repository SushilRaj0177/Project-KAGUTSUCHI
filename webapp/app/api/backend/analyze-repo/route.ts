import { NextRequest, NextResponse } from "next/server";
import { clientIp } from "@/lib/clientIp";

// Proxies to the FastAPI backend server-side. Browser CORS rules only
// apply to fetch() calls made FROM the browser -- routing through our own
// Next.js server means the browser only ever talks to our own origin
// (no CORS involved at all), while this server-to-server call is exempt
// from the CORS preflight that GitHub Codespaces' port-forwarding proxy
// blocks for third-party browser origins.
export const maxDuration = 60;

export async function POST(request: NextRequest) {
  const backendUrl = process.env.KAGUTSUCHI_API_URL;
  if (!backendUrl) {
    return NextResponse.json({ detail: "Backend not configured" }, { status: 503 });
  }

  const body = await request.text();
  try {
    const upstream = await fetch(`${backendUrl.replace(/\/$/, "")}/api/analyze-repo`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Client-IP": clientIp(request) },
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
