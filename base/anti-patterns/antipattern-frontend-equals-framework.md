# ANTI-PATTERN: Frontend Equals Framework

**DOMAIN:** frontend / architecture
**APPEARS AS:** "We need React (or Vue, or Svelte) for the frontend." This is the default assumption in the market: frontend = JavaScript framework. It seems reasonable because frameworks provide component systems, state management, and tooling that appear necessary for "modern" frontends.
**ROOT CAUSE:** Frameworks solve problems that many projects don't have: complex client-side state management, real-time interactivity, SPA navigation. For content-driven sites (blogs, newsletters, documentation, marketing), the problems frameworks solve don't exist — but the complexity they introduce does: build steps, bundle sizes, hydration issues, framework version churn (dies in 18 months).
**RATIONALE:** Akita built a multi-platform frontend (blog, newsletter email, RSS/podcast feed) with: Tailwind CSS v4 for styling (zero JS), Hugo for static site generation, ERB templates for email HTML. The result supports dark mode, responsive design, multiple content types, and multi-platform rendering — without a single line of JavaScript framework code. The same content renders on web, email, and RSS via different pipelines, which would be harder with a framework that couples rendering to its component system.

---

## SYMPTOMS

- Project has a build step for JavaScript but the site is primarily content-driven
- Bundle size exceeds what the actual interactivity requires
- Framework version upgrades consume development time with no user-visible benefit
- Server-side rendering (SSR) is needed to compensate for client-side framework overhead
- Team spends more time on framework tooling than on content or business logic

## CORRECTION

Evaluate the actual interactivity requirements before choosing a framework:
- Content-driven sites → static site generator (Hugo, Jekyll, Eleventy) + utility CSS (Tailwind)
- Server-rendered apps with light interactivity → server framework (Rails, Django, Phoenix) + Hotwire/HTMX/Alpine.js
- Highly interactive applications (dashboards, editors, real-time collaboration) → framework IS appropriate

The best frontend abstraction is often none: HTML + CSS + Markdown. Simple, debuggable, works in 10 years.

**NOT TO CONFUSE WITH:** Choosing NOT to use a framework for a genuinely interactive application (dashboards, collaborative editors, real-time apps). Frameworks exist for a reason — the anti-pattern is using them where they're not needed, not avoiding them everywhere.

## OPERATIONAL CONSTRAINTS
**FOR appropriate frontend technology selection TO SUCCEED:**

NEVER:
- Default to a JavaScript framework without evaluating actual interactivity requirements [explicit — ROOT CAUSE]
- Use a framework for content-driven sites (blogs, newsletters, documentation, marketing) [explicit — CORRECTION]

ALWAYS:
- Evaluate actual interactivity requirements before choosing a framework [explicit — CORRECTION]
- Use static site generators + utility CSS for content-driven sites [explicit — CORRECTION]
- Reserve frameworks for genuinely interactive applications (dashboards, editors, real-time collaboration) [explicit — CORRECTION]

GATE: Project has genuine client-side state management needs (dashboards, editors, real-time collaboration). If false, use static generator + utility CSS.

## SOURCE
https://akitaonrails.com/2026/02/19/frontend-sem-framework-bastidores-do-the-m-akita-chronicles/
