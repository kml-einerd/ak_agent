# PROTOCOL: Sender Reputation Infrastructure

**DOMAIN:** backend / email
**APPLIES TO:** Any application sending emails programmatically — newsletters, transactional emails, notifications — via a commercial sending service such as AWS SES
**RATIONALE:**
1. Email providers (Gmail, Microsoft, Yahoo) use sender reputation signals to classify incoming mail as legitimate or spam. Without correct DNS authentication records, messages are marked suspicious regardless of content. [explicit]
2. DKIM, SPF, and DMARC are three independent but complementary records: SPF declares which servers may send on behalf of your domain; DKIM provides a cryptographic signature proving the email was not altered in transit; DMARC declares a policy for emails that fail SPF or DKIM. All three must pass simultaneously. [explicit]
3. Since February 2024, Gmail enforces additional rules for bulk senders (>5,000 emails/day): List-Unsubscribe and List-Unsubscribe-Post headers are mandatory. Non-compliance penalizes domain reputation across all email categories — including transactional. [explicit]
4. Hard bounces (non-existent addresses) and spam complaints permanently damage sender score. A suppression list tracking these addresses prevents re-sending to them, which would further degrade reputation. [derived]

---

## EVALUATION

| SIGNAL | DIAGNOSE | INTERVENE |
|--------|----------|-----------|
| Gmail marks emails as "suspicious" or "unverified sender" | SPF or DKIM missing or misconfigured in DNS | Add SPF TXT record declaring your sending service (SES generates this). Add 3 CNAME records for DKIM (SES generates these automatically). Verify in DNS before sending. |
| Microsoft/Yahoo increasing rejection rate | DMARC policy absent or set to `none` | Add DMARC TXT record: start with `p=none` to monitor, promote to `p=quarantine` or `p=reject` once reports are clean. |
| Bulk emails (>5k/day to Gmail) land in spam | Missing List-Unsubscribe headers | Add `List-Unsubscribe: <mailto:unsub@yourdomain.com?subject=unsub>` and `List-Unsubscribe-Post: List-Unsubscribe=One-Click` headers to every bulk email. |
| Delivery rate degrades over time despite correct HTML | Hard bounces or complaint events not tracked | Enable SES account-level suppression list. Subscribe to SES bounce/complaint SNS notifications. Reconcile events into delivery records and mark those addresses as bounced/complained. Never re-send to them. |
| SES returns success but subscriber never receives email | Address is on SES internal suppression list | SES silently skips delivery for suppressed addresses but returns success. Check SES suppression list before attributing to other causes. |

**TRADE-OFFS:** Configuring SPF/DKIM/DMARC requires DNS access and propagation wait time (up to 72h). SES suppression list requires SNS event handling infrastructure. The one-time setup cost is low compared to the permanent reputation damage from skipping it.

**ESCALATE WHEN:** Domain reputation is already damaged (spam complaint rate above SES threshold of 0.1%). Recovery requires contacting AWS support and a sending pause — prevention is the only practical strategy.

## SOURCE
https://akitaonrails.com/2026/02/17/enviando-emails-sem-spammar-bastidores-do-the-m-akita-chronicles/
