# Communications System Design (Phase 4)

## Overview
This document outlines the architecture for the notification and communications module in the Perin Devi Natyalayam platform, enabling reliable messaging over WhatsApp (Cloud API) and Email (Amazon SES), handling broadcasts, and generating verifiable certificates.

## References & Documentation Used
- **WhatsApp Cloud API:**
  - Sending messages: https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages
  - Message Templates: https://developers.facebook.com/docs/whatsapp/message-templates/guidelines
  - Webhooks: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples
  - Error Codes: https://developers.facebook.com/docs/whatsapp/cloud-api/support/error-codes
- **Amazon SES via Django Anymail:**
  - Anymail SES Docs: https://anymail.dev/en/stable/esps/amazon_ses/
  - Amazon SES Webhooks (SNS): https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity-using-notifications-sns.html

## 1. Data Model
### MessageTemplate
- Key (e.g. `fee_invoice_issued`)
- Channel (`WHATSAPP` | `EMAIL`)
- Approval Status (`DRAFT` | `APPROVED` | `REJECTED` | `PAUSED`)
- Variables JSON, Body Preview, Category (UTILITY, AUTHENTICATION, MARKETING)

### NotificationPreference
- Per Guardian, Per Category (TRANSACTIONAL, REMINDERS, ANNOUNCEMENTS, MARKETING)
- `whatsapp_enabled`, `email_enabled`
- Default matches Phase 2 Consent records.

### Message & MessageEvent
- **Message**: Central table. Tracks `recipient`, `channel`, `template_key`, `status`, `idempotency_key`, `variables`.
- **MessageEvent**: Append-only log tracking status changes from Webhooks (`SENT`, `DELIVERED`, `READ`, `FAILED`).
- Replaces standard Django signals/hooks for traceability and out-of-order webhook delivery.

### Broadcast
- For bulk scheduling of announcements and marketing to specific segments (e.g. "All Active Students", "Unpaid Dues").
- Explicit 2-step process: Preview (calculate counts & cost) -> Confirm Send.
- Supports Cancellation mid-flight (marks unsent recipients as `SUPPRESSED`).

## 2. Notification Pipeline (`notify` function)
The single entry point `notify(event_key, recipient, ...)` will:
1. **Channel Selection**: Check `NotificationPreference`. For TRANSACTIONAL, WhatsApp requires opt-in; otherwise falls back to email.
2. **Suppression Rules**: Halt sending if opted out, invalid number, or bounce-flagged.
3. **Idempotency**: Block duplicate sends by using deterministic keys (`event_key + recipient_id + object_id`).
4. **Queueing**: Pushes to a Celery task.
5. **Quiet Hours**: Between 21:00 and 07:00 IST, REMINDERS, ANNOUNCEMENTS, and MARKETING are delayed to 07:00. Time-critical reminders that exceed expiry are marked `EXPIRED`. TRANSACTIONAL (OTP, receipts) ignore quiet hours.

## 3. Retries & Fallback
- **Transient Errors** (Network, 429, 5xx): Celery exponential backoff with jitter. Max 3-5 attempts.
- **Permanent Errors** (Invalid number, template rejected): Fails immediately.
- **Fallback**: If a WhatsApp transactional message fails permanently or exhausts retries, it triggers an email fallback (linked via `fallback_of`).

## 4. Webhook Security & Handling
- **WhatsApp**:
  - Handshake verifies `hub.verify_token`.
  - POST requests verify `X-Hub-Signature-256` using constant-time HMAC comparison on the raw body.
  - Out-of-order status updates handled gracefully (e.g., a late `SENT` webhook will not overwrite a `READ` status).
- **Email (SES)**: Validated via Anymail's built-in SES SNS signature verification.

## 5. Opt-Outs & Inbound Messages
- **STOP / UNSUBSCRIBE**: Instantly marks the guardian as opted out of MARKETING/ANNOUNCEMENTS and revokes `ConsentRecord`.
- **START**: Re-subscribes.
- Unrecognized inbound messages are stored in `InboundMessage` for admin review. No automated free-text replies.

## 6. Certificates & Tracked Links
- **Certificates**: Reusing Phase 1 verification concepts but standardizing templates using WeasyPrint (HTML -> PDF). Issued with UUID tokens.
- **Tracked Links**: Secure HMAC-signed URLs generated for class reminders. Prevents link sharing. Validates the logged-in guardian/student before redirecting to the actual meeting URL.
