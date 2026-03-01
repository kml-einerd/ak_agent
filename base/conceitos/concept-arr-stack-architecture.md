# CONCEPT: Arr Stack Architecture

**DOMAIN:** deployment / self-hosting / architecture
**DEFINITION:** The "arr stack" is a composable set of self-hosted services that together automate the full lifecycle of personal media: discovery → acquisition → organization → streaming. Each service has a single responsibility and communicates with the others via internal HTTP APIs. The stack is named after the "-arr" suffix common to its core components (Radarr, Sonarr, Prowlarr, Bazarr, Lidarr). The key architectural property is that **no single component spans more than one responsibility** — Prowlarr knows indexers but not downloads; Radarr knows what movies to get but not how to find indexers; QBitTorrent downloads but does not decide what to download.
**NOT:**
- Not a monolithic media center application — each service is independently deployable and replaceable
- Not a streaming platform — Plex (or Jellyfin/Emby) is the streaming layer, entirely separate from acquisition
- Not a legal service by default — the stack is infrastructure-agnostic; legality depends on what indexers and content are configured
**RATIONALE:** Without this named concept, the stack appears to be a collection of independent apps. The architectural insight is that the separation of concerns between indexer management (Prowlarr), media management (Radarr/Sonarr), download execution (QBitTorrent), subtitle sourcing (Bazarr), request interface (Overseerr), and streaming (Plex) is intentional design — each component can be upgraded or replaced without rebuilding the whole system. This is the composable self-hosting pattern.

---

## REFERENCED BY

- base/procedimentos/procedure-arr-stack-personal-media-server.md

## SOURCE
https://akitaonrails.com/2024/04/03/meu-netflix-pessoal-com-docker-compose/
