import type { NextRequest } from "next/server";

/** Vercel sets x-forwarded-for on every request reaching a route handler.
 * Requests to the FastAPI backend go server-to-server from here, so
 * without forwarding this the backend would only ever see Vercel's own
 * egress IP for every visitor -- making per-IP rate limiting meaningless.
 * First entry in the list is the original client. */
export function clientIp(request: NextRequest): string {
  const forwarded = request.headers.get("x-forwarded-for");
  if (forwarded) return forwarded.split(",")[0].trim();
  return "unknown";
}
