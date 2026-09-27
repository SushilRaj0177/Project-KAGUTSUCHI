import { NextRequest, NextResponse } from "next/server";
import { clientIp } from "@/lib/clientIp";
import { auth } from "@/lib/auth";

// Proxies straight through to the FastAPI backend's /api/open-pr — same
// server-to-server pattern as every other route in app/api/backend/*
// (see analyze-repo/route.ts).
//
// The request body carries a github_token field. If the caller is signed
// in via GitHub OAuth (see lib/auth.ts), that session's real access
// token is substituted here server-side, overriding whatever the client
// sent — the token then never has to touch client JS at all for a
// signed-in user. The old paste-a-PAT flow (FindingCard.tsx) still works
// unmodified for anyone not signed in: this route just forwards whatever
// they typed in that case, reading it only as opaque bytes, never
// parsing, logging, or persisting it.
export const maxDuration = 30;

export async function POST(request: NextRequest) {
  const backendUrl = process.env.KAGUTSUCHI_API_URL;
  if (!backendUrl) {
    return NextResponse.json({ detail: "Backend not configured" }, { status: 503 });
  }

  const session = await auth();
  let bodyText = await request.text();

  if (session?.accessToken) {
    try {
      const parsed = JSON.parse(bodyText);
      bodyText = JSON.stringify({ ...parsed, github_token: session.accessToken });
    } catch {
      // malformed body - let the backend reject it normally
    }
  }

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
