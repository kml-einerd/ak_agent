# HEURISTIC: Email Prefers At-Most-Once Delivery

**DOMAIN:** backend / email
**RULE:** For email delivery, prefer at-most-once semantics over at-least-once: when the delivery outcome is unknown, do not auto-retry. One missed email is always less harmful than one duplicate.
**APPLIES WHEN:** Designing email delivery state machines where a process may die between the send call and the confirmation write — newsletters, transactional notifications, any non-idempotent email send.
**RATIONALE:**
1. At-least-once delivery guarantees every recipient receives the email but accepts duplicates as the failure mode. At-most-once delivery accepts that some emails may be lost but never duplicates. [explicit]
2. For most programmatic emails, receiving the same message twice damages user trust and may trigger spam complaints. One duplicate newsletter is an annoyance; ten duplicates get the domain blacklisted. [derived]
3. The heuristic-ambiguous-state-no-retry rule applies directly: when a worker dies between send and confirmation, the correct state is "unknown" requiring manual review, not "pending" triggering automatic retry. [explicit]
**COUNTER-INDICATION:** Does not apply to idempotent notifications (e.g., a daily digest where receiving a second copy causes no harm) or to systems with strict delivery SLAs where every missed delivery is a business violation.

## SOURCE
https://akitaonrails.com/2026/02/17/enviando-emails-sem-spammar-bastidores-do-the-m-akita-chronicles/
