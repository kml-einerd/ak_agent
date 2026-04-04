# PROCEDURE: HSL Color Palette Design

**TRIGGER:** Need to create a harmonious multi-color palette for a project with multiple visual sections, themes (light/dark), and accessibility requirements
**DOMAIN:** frontend / design-system
**PRE-CONDITIONS:** Project has multiple distinct sections or categories requiring unique colors. Target includes both light and dark themes. WCAG compliance is desired.

---

## STEPS

1. Identify the number of distinct sections/categories → count of required unique colors (e.g., 8 sections = 8 hues)
2. Distribute hues evenly around the 360° HSL color wheel → e.g., 8 colors = every 45° (0°, 35°, 45°, 140°, 180°, 210°, 225°, 270°) — equidistant hues create visual harmony
3. Define saturation and lightness rules per visual layer:
   - Light theme backgrounds: ~92-95% lightness, ~25% saturation (pastel, no section "screams")
   - Light theme text: ~15-20% lightness (ensures >7:1 contrast ratio = WCAG AAA)
   - Dark theme backgrounds: ~10-12% lightness (uniform depth)
   - Dark theme text: ~80-85% lightness (ensures >6:1 contrast ratio = WCAG AA)
   - Borders (both themes): ~45-55% lightness (accent, visible but not dominant)
4. Apply rules: for each hue, generate the full color set by plugging the hue into fixed S/L values → deterministic palette, no subjective decisions
5. Verify contrast ratios using WCAG checker tools → background/text pairs must meet AA (4.5:1) minimum, AAA (7:1) preferred
6. Document the rules as a code comment for future maintainers → six rules, N hues, two themes, 100% deterministic

**ON_FAILURE[step-5]:** If contrast fails, adjust lightness by 5% increments until ratio meets threshold. Never adjust hue — it breaks the harmonic distribution.

---

## DONE WHEN
- All color pairs (background + text) pass WCAG AA contrast ratio (4.5:1 minimum), verified with a contrast checker tool
- Adding a new section requires only picking an unoccupied hue and applying the same S/L rules — no subjective color decisions needed

## SOURCE
https://akitaonrails.com/2026/02/19/frontend-sem-framework-bastidores-do-the-m-akita-chronicles/
