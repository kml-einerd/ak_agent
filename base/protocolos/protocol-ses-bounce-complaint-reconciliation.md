# PROTOCOL: SES Bounce Complaint Reconciliation

**DOMAIN:** backend / email
**APPLIES TO:** Applications using AWS SES for email delivery that track per-recipient delivery state in a database
**RATIONALE:**
1. SES does not block the sending call when a bounce or complaint occurs — it delivers the event asynchronously via SNS notifications, often seconds or minutes after the send. A delivery record written as "sent" may need to be retroactively corrected. [explicit]
2. SES adds hard-bounced and complained addresses to an account-level suppression list and silently skips them on future sends while returning success. Without reconciliation, your local delivery records diverge from SES reality. [explicit]
3. Reconciling SES events back into delivery records closes the loop: the application's state matches what SES actually did, enabling correct retry decisions and protecting domain reputation by not re-sending to addresses that generated complaints. [derived]

---

## EVALUATION

| SIGNAL | DIAGNOSE | INTERVENE |
|--------|----------|-----------|
| Delivery record status is "sent" but subscriber reports no receipt | Address may be on SES suppression list | Query SES suppression list for the address. If present, the delivery never happened — update local record to "suppressed" and investigate how the address entered suppression. |
| SES SNS event arrives with bounce type "Permanent" | Non-existent or unreachable address | Look up the EmailDelivery record by recipient address. Update status to "bounced". Add address to local suppression table. Do not send further to this address. |
| SES SNS event arrives with complaint type "abuse" | Subscriber marked as spam | Look up the EmailDelivery record. Update status to "complained". Immediately add to local suppression. Update subscriber record to prevent future sends. |
| High bounce rate appearing in SES metrics | Stale subscriber list with invalid addresses | Run reconciliation job against SES bounce events for the last 30 days. Purge or deactivate bounced subscribers from the mailing list. |
| SES account flagged / sending paused | Complaint or bounce rate exceeded SES thresholds | Stop sending immediately. Reconcile all recent delivery records against SES events. Remove offending addresses. Contact AWS support to restore sending. |

**TRADE-OFFS:** Requires SNS topic subscription and webhook endpoint to receive SES events. Adds operational complexity. Without this reconciliation, the application has no accurate view of actual delivery state.

**ESCALATE WHEN:** SES suppression list contains addresses that were never sent to by this application — indicates cross-account contamination or a DNS misconfiguration being shared across sending identities.

## SOURCE
https://akitaonrails.com/2026/02/17/enviando-emails-sem-spammar-bastidores-do-the-m-akita-chronicles/
