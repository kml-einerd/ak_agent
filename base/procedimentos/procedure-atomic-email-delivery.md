# PROCEDURE: Atomic Email Delivery

**TRIGGER:** Need to send emails to multiple recipients in a way that survives server restarts, network failures, and process crashes without duplicating or losing deliveries
**DOMAIN:** backend / email
**PRE-CONDITIONS:** A database is available for tracking delivery state. Email sending service (SES, Sendgrid, etc.) is configured. The email content is ready to send.

---

## STEPS

1. Create one delivery record per recipient with status "pending" → `EmailDelivery.create!(newsletter: newsletter, subscriber: sub, status: "pending")` — batch insert all recipients before sending any email
2. For each delivery, perform atomic claim: lock the record, update status to "sending" → `delivery = EmailDelivery.where(status: ["pending", "failed"]).lock.first; delivery.update!(status: "sending")`
3. Send the email → call the email service with the recipient's address and content
4. Update status to "sent" on success → `delivery.update!(status: "sent")`
5. On send failure, update status to "failed" → the record will be picked up again by step 2 on next iteration
6. Schedule a recovery job (RecoverStaleDeliveriesJob) to run periodically → finds records stuck in "sending" status beyond a timeout and moves them to "unknown" status

**ON_FAILURE[step-3]:** If the email service returns a permanent error (invalid address, rejected), mark as "failed_permanent" — do not retry
**ON_FAILURE[between step-3 and step-4]:** If the server dies between sending and confirming, the record stays as "sending". The recovery job will mark it "unknown". NEVER auto-resend emails in "unknown" state — they may have been delivered.

---

## DONE WHEN
- All delivery records are in a terminal state: "sent", "failed_permanent", or "unknown" (verified by `SELECT count(*) FROM email_deliveries WHERE status NOT IN ('sent','failed_permanent','unknown')` returning 0)
- No emails were sent twice (verified by checking delivery logs for duplicate recipient+newsletter pairs)
- Server restart during the process results in resumption from where it stopped, not from the beginning (verified by killing the process mid-run and confirming already-sent records are not re-sent)

## SOURCE
https://akitaonrails.com/2026/02/19/jobs-asssincronos-que-sobrevivem-ao-caos-bastidores-do-the-m-akita-chronicles/
