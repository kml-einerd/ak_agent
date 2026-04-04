# PROCEDURE: Dual Content Render Pipeline

**TRIGGER:** Same content (articles, newsletters) needs to be published to both a website and email, with different rendering requirements for each target
**DOMAIN:** architecture / content-publishing
**PRE-CONDITIONS:** Content is authored in Markdown (or similar universal format). Website engine and email system are separate services. Shortcodes or custom components are used in the web version.

---

## STEPS

1. Define Markdown + YAML frontmatter as the single source of truth → all content lives in one format, consumed by multiple renderers
2. Build web pipeline: static site generator (Hugo, Jekyll, etc.) processes Markdown with shortcodes, CSS classes, responsive images, dark mode via media queries → web-optimized output
3. Build email pipeline: server-side processor (Rails ERB, Node, etc.) converts same Markdown to email-safe HTML:
   - Strip or convert shortcodes to inline HTML equivalents (each shortcode needs an email-safe mapping)
   - Convert CSS classes to inline styles (email clients ignore `<style>` tags)
   - Rewrite relative image URLs to absolute URLs
   - Replace responsive layout with `<table>` layout (Outlook uses Word engine)
   - Apply theme via server-side variables (not media queries — most email clients don't support them)
4. Store shortcode→email-safe mappings in a hash/config → SHORTCODE_PATTERNS maps each shortcode regex to an inline HTML template
5. Test email output in multiple clients (Gmail, Outlook, Apple Mail, Yahoo) using tools like Email on Acid or Litmus → verify rendering and spam scoring

**ON_FAILURE[step-3]:** If a shortcode has no reasonable email equivalent, remove it cleanly (don't leave raw shortcode syntax in email)
**ON_FAILURE[step-5]:** If Outlook breaks the layout, switch that section to `<table>` structure — Outlook renders HTML with the Word engine

---

## DONE WHEN
- Same Markdown file produces correct output on both web and email (verified by rendering a test article through both pipelines)
- Adding a new shortcode requires adding one web template AND one email-safe mapping (no other files need changes)
- Email output passes WCAG contrast and renders correctly in Gmail, Outlook, and Apple Mail (verified via email testing tool)

## SOURCE
https://akitaonrails.com/2026/02/19/frontend-sem-framework-bastidores-do-the-m-akita-chronicles/
