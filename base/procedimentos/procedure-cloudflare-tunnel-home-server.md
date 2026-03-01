# PROCEDURE: Cloudflare Tunnel Home Server

**TRIGGER:** You need to expose a home server service (Docker container, NAS, local app) to the internet without opening router ports or revealing your home IP.
**DOMAIN:** security / deployment / self-hosting
**PRE-CONDITIONS:**
- Domain registered and nameservers delegated to Cloudflare
- Docker installed on the home server
- A Cloudflare account (free tier is sufficient for small personal use)

---

## STEPS

1. In Cloudflare dashboard (one.dash.cloudflare.com), navigate to **Networks → Tunnels → Create a tunnel** → choose "Cloudflared" connector → name the tunnel → copy the generated `TUNNEL_TOKEN` value.
   → Expected output: token string available for use in docker-compose

2. Add the `cloudflared` container to your `docker-compose.yml`:
   ```yaml
   cloudflared:
     image: cloudflare/cloudflared:latest
     command: tunnel --no-autoupdate run
     environment:
       - "TUNNEL_TOKEN=${TUNNEL_TOKEN}"
     restart: unless-stopped
   ```
   → Expected output: cloudflared connects outbound to Cloudflare edge; no inbound ports required

3. In the Cloudflare Tunnel dashboard, configure a **Public Hostname** for each service:
   - Subdomain: e.g. `portainer`
   - Domain: your Cloudflare-managed domain
   - Service: `http://localhost:9000` (or the internal container address/port)
   → Expected output: Cloudflare creates a CNAME DNS record pointing to the tunnel

4. Verify the service is reachable via `https://portainer.yourdomain.com` from an external network (e.g. phone on mobile data).
   → Expected output: HTTPS page loads without any open router port

5. Enable **Cloudflare Zero Trust Access** for each hostname:
   - Go to Zero Trust dashboard → **Access → Applications → Add an Application**
   - Select "Self-hosted", enter the subdomain, set **Session Duration**
   - In **Policies**, create an Allow policy with identity provider condition (e.g. "Emails ending in @yourdomain.com")
   → Expected output: Cloudflare login wall appears before reaching the service

6. Configure **Google OAuth** as identity provider (if using Google Workspace):
   - In Google Cloud Console: **APIs & Services → Credentials → Create OAuth Client ID** (Web Application type)
   - Add **Authorized JavaScript Origins**: `https://[your-team-name].cloudflareaccess.com`
   - Copy **Client ID** and **Client Secret**
   - In Zero Trust dashboard: **Settings → Authentication → Add Login Method → Google** → paste Client ID as "App ID" and Client Secret
   → Expected output: Users must authenticate with Google before accessing any protected service

**ON_FAILURE[step-2]:** If cloudflared container fails to start, verify TUNNEL_TOKEN is correctly set in `.env` file and the token has not expired in the dashboard.

**ON_FAILURE[step-4]:** If service returns 502/tunnel error, confirm the internal service address and port in the Public Hostname config matches the actual running container.

**ON_FAILURE[step-6]:** If OAuth login loop occurs, verify the Authorized JavaScript Origins URL exactly matches the Cloudflare Access team domain (no trailing slash, correct subdomain).

---

## DONE WHEN
- Each service is accessible via HTTPS subdomain from external networks without open router ports
- Unauthenticated requests are blocked by Cloudflare login wall before reaching the service
- Google/identity login is required on first access and on session expiry
- No port forwarding rules exist in the home router for these services

## SOURCE
https://akitaonrails.com/2025/09/10/protegendo-seu-home-server-com-cloudflare-zero-trust/
