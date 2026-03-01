# PROTOCOL: Zero Trust Access Layer

**DOMAIN:** security / self-hosting / architecture
**APPLIES TO:** Any home server or internal service exposed via a public URL, regardless of the transport mechanism (tunnel, VPN, reverse proxy)
**RATIONALE:**
1. Services exposed through tunnels or reverse proxies are still reachable by anyone who knows the URL — the transport security (TLS, tunnel encryption) does not prevent unauthorized use of the service itself. [explicit]
2. Adding an identity-layer gate (Zero Trust Access, Authelia, OAuth proxy) in front of each service means authentication happens at the edge before a single byte reaches the application, eliminating the "authenticated tunnel, unauthenticated app" failure mode. [explicit]
3. Identity providers with Google Workspace or email-domain policies allow fine-grained allowlisting without maintaining a separate user database — the identity provider is the source of truth. [derived]

---

## EVALUATION

| SIGNAL | DIAGNOSE | INTERVENE |
|--------|----------|-----------|
| Service URL is reachable without any login prompt | No auth layer configured — anyone with the URL can reach the app | Add Zero Trust Access policy to the hostname before making URL public |
| Service has its own login but no outer gate | Single-layer auth — credential brute-force attacks reach the app directly | Add identity-provider gate at Cloudflare/reverse-proxy layer as outer wall |
| Multiple services on same tunnel with different access requirements | Flat policy applies same auth to all — admin panel and public app treated equally | Create per-hostname Access policies with different identity conditions per service |
| OAuth redirect loop or 401 on first login | Identity provider OAuth credentials misconfigured (wrong Origins URL or Client ID) | Verify Authorized JavaScript Origins in Google Cloud exactly matches Cloudflare Access team domain |
| Session expiry forces re-login too frequently | Session duration set too short | Increase session duration in Access policy (24h for personal use, lower for sensitive admin services) |

**TRADE-OFFS:**
- Gain: Zero-knowledge exposure of home network; Cloudflare absorbs DDoS, WAF, bot mitigation before traffic touches your server
- Lose: Dependency on Cloudflare free tier limits (number of seats, applications); if Cloudflare has an outage, all services become unreachable even from LAN-adjacent paths

**ESCALATE WHEN:** Service requires server-to-server calls or machine credentials (not human OAuth) — Zero Trust Access policies designed for human SSO do not fit service accounts; use Cloudflare Service Tokens or mTLS instead.

## SOURCE
https://akitaonrails.com/2025/09/10/protegendo-seu-home-server-com-cloudflare-zero-trust/
