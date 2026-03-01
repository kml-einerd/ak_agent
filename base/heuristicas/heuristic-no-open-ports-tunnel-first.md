# HEURISTIC: No Open Ports — Tunnel First

**DOMAIN:** security / self-hosting / deployment
**RULE:** When exposing a home server service to the internet, never open router ports — use an outbound tunnel (Cloudflare Tunnel or equivalent) as the default approach.
**APPLIES WHEN:** Any scenario where a home server, NAS, or local Docker service needs to be publicly accessible; particularly when the host is behind a residential ISP with dynamic IP.
**RATIONALE:**
1. Opening inbound router ports exposes the home IP address directly, making the server discoverable and attackable from the entire internet; each open port is an attack surface that requires ongoing maintenance (firewall rules, fail2ban, rate limiting). [explicit]
2. An outbound tunnel (cloudflared) reverses the connection direction: the agent on your server connects outward to Cloudflare's edge, so no inbound path exists. Attackers cannot reach your home IP because no route exists in the router. [explicit]
3. Combining the tunnel with Zero Trust Access adds a hard authentication gate at Cloudflare's edge — the attack must breach Cloudflare before it reaches your LAN, which eliminates the entire class of "unauthenticated exposure" vulnerabilities from misconfigured services. [derived]
**COUNTER-INDICATION:** This rule does not apply when the service must accept arbitrary inbound connections (e.g. a game server, a mail server receiving SMTP) where the protocol does not work through an HTTP-based tunnel proxy. In those cases, open the minimal port set and apply strict rate limiting.

## SOURCE
https://akitaonrails.com/2025/09/10/protegendo-seu-home-server-com-cloudflare-zero-trust/
