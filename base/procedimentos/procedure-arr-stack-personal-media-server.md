# PROCEDURE: Arr Stack Personal Media Server

**TRIGGER:** You want to build a self-hosted personal media server that automatically acquires, organizes, and streams movies and TV series — equivalent to a personal Netflix/streaming service.
**DOMAIN:** deployment / self-hosting / media
**PRE-CONDITIONS:**
- A machine with substantial storage (NAS, desktop, server — Akita uses Synology DS1821+ with ~80TB raw, 50TB+ used)
- Docker and Docker Compose installed
- Plex account (free tier works; Plex Pass unlocks hardware transcoding)
- Sufficient upstream bandwidth or local network for streaming

---

## STEPS

1. Deploy **Portainer** (port 9000) for Docker container management UI — provides centralized control over all services.
   → Expected output: Web-based Docker management interface accessible at `http://[server]:9000`

2. Deploy **Prowlarr** as the centralized indexer aggregator — connect all torrent/usenet indexers once here, and Radarr/Sonarr inherit them automatically.
   → Expected output: Single indexer management point; eliminates per-app indexer configuration duplication

3. Deploy **Radarr** (movies) and **Sonarr** (TV series) as automated media managers:
   - Configure quality profiles (e.g. 1080p BluRay, 4K HDR)
   - Connect to Prowlarr for indexer search
   - Connect to QBitTorrent as download client
   → Expected output: Radarr/Sonarr automatically search, evaluate quality, and queue downloads through QBitTorrent

4. Deploy **QBitTorrent** (port 6881) as the download client integrated with the arr stack.
   → Expected output: Downloads land in configured watched folder; Radarr/Sonarr detect and move completed files to media library

5. Deploy **FlareSolverr** alongside Prowlarr if indexers are behind Cloudflare bot protection — it handles CAPTCHA-protected indexer pages automatically.
   → Expected output: Prowlarr can reach Cloudflare-protected indexers without manual intervention

6. Deploy **Plex Media Server** — point libraries at the organized media folders populated by Radarr/Sonarr.
   → Expected output: Plex catalogs all media, generates metadata, posters, subtitles; streams to any device via Plex client apps

7. Deploy **Overseerr** as the request interface — users submit movie/series requests here; Overseerr forwards to Radarr or Sonarr automatically.
   → Expected output: Non-technical household members can request content without accessing Radarr/Sonarr directly

8. Deploy **Bazarr** for automatic subtitle acquisition — connects to Plex library, downloads matching subtitles in configured languages for all items.
   → Expected output: Subtitles present for all media without manual search

9. Deploy **MakeMKV + HandBrake** for physical media digitization:
   - MakeMKV: decrypts and rips BluRay/DVD to MKV
   - HandBrake: transcodes MKV to compressed format for storage efficiency
   → Expected output: Physical collection converted to streamable files in the Plex library

**ON_FAILURE[step-2]:** If Radarr/Sonarr cannot search, verify Prowlarr sync is enabled under each app's indexer settings (not just added — it must be synced).

**ON_FAILURE[step-4]:** If completed downloads are not picked up by Radarr/Sonarr, verify the download client's category and the completed downloads path match the watch folder configured in each arr app.

**ON_FAILURE[step-6]:** If Plex does not find metadata, verify library path exactly matches the folder structure Radarr/Sonarr use (e.g. `/movies/Film Title (Year)/Film Title (Year).mkv`).

---

## DONE WHEN
- Requesting a movie in Overseerr triggers automatic download and the movie appears in Plex within minutes of download completion
- Sonarr detects new episodes automatically and adds them to Plex without manual action
- Subtitle files are present alongside media files for configured languages
- All services are accessible via Portainer and restart automatically after server reboot (`restart: unless-stopped` in compose)

## SOURCE
https://akitaonrails.com/2024/04/03/meu-netflix-pessoal-com-docker-compose/
