import type { MiddlewareResponseHandler } from "astro";
import { validateAdminSession } from "@astrobranding/database";

export const onRequest: MiddlewareResponseHandler = async (context, next) => {
  const host =
    context.request.headers.get("x-forwarded-host") ||
    context.request.headers.get("host") ||
    "";

  if (host.includes("staging.")) {
    // Staging environment (sandbox credentials, test gateways)
    context.locals.environment = "stage";
    context.locals.isProduction = false;
  } else if (
    host.includes("zerops.app") ||
    host.includes("localhost") ||
    host.includes("127.0.0.1")
  ) {
    // Development / Ephemeral preview environment
    context.locals.environment = "dev";
    context.locals.isProduction = false;
  } else {
    // Production environment (live traffic, strict caching)
    context.locals.environment = "prod";
    context.locals.isProduction = true;
  }

  // Always validate admin session if cookie is present (covers both /adminn/* and /_actions/*)
  const sessionCookie = context.cookies.get("admin_session")?.value;
  let adminUser = null;

  if (sessionCookie) {
    try {
      const user = await validateAdminSession(sessionCookie);
      if (user) {
        adminUser = {
          id: user.id,
          name: user.name,
          role: user.role,
          telegramUserId: Number(user.telegramUserId),
        };
      }
    } catch (err) {
      console.error("[Middleware] Admin session check error:", err);
    }
  }

  context.locals.adminUser = adminUser;

  const url = new URL(context.request.url);
  const isAdminRoute = url.pathname === "/adminn" || url.pathname.startsWith("/adminn/");

  if (isAdminRoute) {
    // Route guards
    if (url.pathname === "/adminn" || url.pathname === "/adminn/") {
      if (adminUser) {
        return context.redirect("/adminn/dashboard");
      }
    } else if (url.pathname.startsWith("/adminn/")) {
      if (!adminUser) {
        return context.redirect("/adminn");
      }
    }
  }

  const response = await next();

  if (isAdminRoute) {
    response.headers.set("X-Robots-Tag", "noindex, nofollow, noarchive");
    response.headers.set("X-Frame-Options", "DENY");
    response.headers.set("X-Content-Type-Options", "nosniff");
    response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
    response.headers.set("Cache-Control", "private, no-cache, no-store, must-revalidate");
    response.headers.set("Pragma", "no-cache");
    response.headers.set("Expires", "0");
  }

  return response;
};
