# PROTOCOL: Email HTML Compatibility

**DOMAIN:** frontend / email
**APPLIES TO:** Building HTML emails that must render correctly across email clients AND avoid spam filters. Applies to newsletters, transactional emails, and any programmatically generated email with custom HTML.
**RATIONALE:** Email clients are the worst rendering environment in web development. Outlook 2016+ uses the Microsoft Word engine for HTML rendering. Gmail strips `<style>` tags. Yahoo has unique quirks. The same HTML practices that ensure correct rendering also signal legitimacy to spam filters — because spammers produce the opposite: malformed HTML, hidden text, image-heavy content. Following rendering best practices simultaneously solves deliverability.

---

## EVALUATION

| SIGNAL | DIAGNOSE | INTERVENE |
|--------|----------|-----------|
| Layout breaks in Outlook | Using `display: flex`, `grid`, or modern CSS layout | Replace with `<table>` layout. Outlook only reliably supports table-based layouts. |
| Styles not applied in Gmail | Using `<style>` tag for CSS | Convert ALL CSS to inline styles on each element. Gmail strips `<style>` tags. |
| Images have wrong dimensions in some clients | Using CSS for image sizing | Add explicit `width` and `height` attributes on `<img>` tags. Use `padding` on parent `<td>` instead of `margin` on images. |
| Email lands in spam folder | Multiple possible causes — check HTML quality | Verify: (1) all tags properly closed/nested, (2) text:image ratio ≥ 60:40, (3) all `<img>` have descriptive `alt`, (4) no `display:none` or hidden text, (5) HTML < 100KB, (6) link text matches link href domain |
| Dark mode looks wrong | Using `prefers-color-scheme` media query | Don't rely on automatic dark mode detection in email. Let subscriber choose theme at signup. Apply theme server-side via template variables. |
| Custom fonts don't render | Using web fonts | Use system font stack: `font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;` |

**TRADE-OFFS:** Table-based layout and inline CSS are verbose and harder to maintain, but are the only reliable approach for cross-client email rendering. The investment in proper email HTML pays off in both rendering quality and deliverability.

**ESCALATE WHEN:** Email consistently lands in spam despite following all HTML best practices — the issue may be domain reputation, SPF/DKIM/DMARC configuration, or sending volume patterns rather than HTML quality.

## SOURCE
https://akitaonrails.com/2026/02/19/frontend-sem-framework-bastidores-do-the-m-akita-chronicles/
