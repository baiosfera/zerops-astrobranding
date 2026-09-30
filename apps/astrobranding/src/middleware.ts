import { defineMiddleware } from "astro:middleware";

export const onRequest = defineMiddleware(async (context, next) => {
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

  return next();
});
