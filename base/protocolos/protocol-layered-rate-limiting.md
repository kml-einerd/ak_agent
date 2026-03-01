# PROTOCOL: Layered Rate Limiting

**DOMAIN:** security
**APPLIES TO:** Any web application with public-facing endpoints, especially those with authentication, file download, or API access
**RATIONALE:**
1. Attack vectors target different stack levels: brute-force targets specific endpoints, enumeration targets resource patterns, volumetric abuse targets the IP level [explicit]
2. A single rate limit at one level (e.g., global IP throttle) cannot distinguish between a login brute-force and legitimate browsing — it either blocks legitimate users or allows targeted attacks through [derived]
3. Layering limits (per-endpoint + per-email + per-resource + global) means each individual limit can be more permissive because other layers provide backup, and outer layers (middleware) reject bad traffic before the application wastes compute processing it [explicit]

---

## EVALUATION

| SIGNAL | DIAGNOSE | INTERVENE |
|--------|----------|-----------|
| Same IP makes 100+ requests to login endpoint in 1 minute | Credential brute-force attack | Middleware throttle: 5 attempts/minute per IP on login path (Rack::Attack, nginx limit_req) |
| Same email targeted from multiple IPs | Distributed credential stuffing | Controller-level throttle by email: 5 attempts/minute per email (Rails 8 rate_limit) |
| IP tries many random download hashes in rapid succession | Hash enumeration attack | Per-resource throttle + automated IP ban after N invalid attempts (cache counter + Ban model) |
| General high request volume from single IP (not targeting specific endpoint) | Volumetric abuse or scraping | Global throttle: 300 requests/5 minutes per IP excluding static assets |
| Legitimate user hits rate limit during normal use | Limits too aggressive for the use case | Make limits configurable per environment: production 1x, development 10x to prevent self-lockout during testing |

**TRADE-OFFS:** Multiple rate limiting layers add configuration complexity and potential for legitimate users hitting unexpected limits. However, layered defense means each individual limit can be more permissive because other layers provide backup. IPs banned at middleware level never reach the application, saving resources.

**ESCALATE WHEN:** Attack volume exceeds what application-level rate limiting can handle. Move to infrastructure-level protection (Cloudflare, AWS WAF) or dedicated DDoS mitigation. Also escalate when rate limiting interferes with legitimate automated clients (CI/CD, monitoring).

## SOURCE
https://akitaonrails.com/2026/02/21/vibe-code-fiz-um-clone-do-mega-em-rails-em-1-dia-pro-meu-home-server/
