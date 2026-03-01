# PROCEDURE: File Upload Sanitization Pipeline

**TRIGGER:** Application accepts file uploads from users
**DOMAIN:** security
**PRE-CONDITIONS:** Server-side file handling is implemented; MIME detection library available (e.g., Marcel for Ruby, python-magic for Python)

---

## STEPS

1. Strip path traversal with File.basename (../../etc/passwd → passwd) → filename contains no directory separators
2. Handle invalid UTF-8 by replacing invalid/undefined bytes with empty string → filename is valid UTF-8
3. Remove control characters and unsafe filesystem chars (null bytes, \x00-\x1f, \x7f, /, \, :, *, ?, ", <, >, |) → filename contains only safe printable characters
4. Strip leading dots to prevent hidden file creation (.evil → evil) → no hidden files created
5. Check for Windows reserved device names (CON, PRN, AUX, NUL, COM1-9, LPT1-9) and prefix with underscore if matched → safe on NTFS/Windows filesystems
6. Strip extension junk from URL-derived filenames (photo.jpg_1280x720+quality=80 → photo.jpg) → extension reflects actual file type
7. Truncate filename to 255 bytes (not characters — a 4-byte emoji counts as 4) while preserving extension → compatible with ext4/NTFS limits
8. Detect MIME type server-side from file magic bytes (Marcel, not client Content-Type header) → actual file type determined independently of client claims
9. Measure file size from tempfile on disk (not Content-Length header which can be forged) → actual file size known
10. Apply client-side pre-validation (size, filename characters) as UX convenience only — never as security boundary → fast user feedback without trusting client

**ON_FAILURE[step-7]:** If filename becomes empty after sanitization, use fallback "unnamed_file"
**ON_FAILURE[step-8]:** If MIME detection fails, reject upload rather than guessing type

---

## DONE WHEN
Every uploaded file has: sanitized filename safe for all target filesystems, server-verified MIME type, server-measured file size, and passes quota check against user's disk allocation.

## SOURCE
https://akitaonrails.com/2026/02/21/vibe-code-fiz-um-clone-do-mega-em-rails-em-1-dia-pro-meu-home-server/
