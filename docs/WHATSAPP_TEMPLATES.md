# WhatsApp Templates Design

## Overview
Proposed WhatsApp templates for Phase 4. All texts strictly adhere to Meta's Business Messaging guidelines. Variables are formatted as `{{1}}`, `{{2}}`.

## 1. Authentication (OTP)
**Name:** `otp_delivery`
**Category:** AUTHENTICATION
**Language:** en
**Body:**
```
Your Perin Devi Natyalayam login code is {{1}}.

Do not share this code with anyone. It expires in 5 minutes.
```
*Button:* Copy Code `{{1}}`

## 2. Utility (Transactional & Reminders)
Promotional words are strictly avoided in UTILITY templates.

**Name:** `welcome_admission`
**Category:** UTILITY
**Language:** en
**Body:**
```
Dear {{1}},

Welcome to Perin Devi Natyalayam! The admission for {{2}} is confirmed.
Your student ID is: {{3}}.

You can access the student portal to view schedules, attendance, and fees.
```
*Button:* Log In to Portal

**Name:** `class_reminder`
**Category:** UTILITY
**Language:** en
**Body:**
```
Reminder: {{1}}'s dance class ({{2}}) starts at {{3}}.

Please join on time.
```
*Button (URL):* Join Class `https://{domain}/portal/join/{{4}}`

**Name:** `class_cancelled`
**Category:** UTILITY
**Language:** en
**Body:**
```
Dear {{1}},

The class for {{2}} scheduled on {{3}} at {{4}} has been cancelled.
Reason: {{5}}

We apologize for any inconvenience.
```

**Name:** `class_rescheduled`
**Category:** UTILITY
**Language:** en
**Body:**
```
Dear {{1}},

The class for {{2}} originally scheduled on {{3}} has been rescheduled.
New Date & Time: {{4}} at {{5}}.
```

**Name:** `absence_alert`
**Category:** UTILITY
**Language:** en
**Body:**
```
Dear {{1}},

{{2}} was marked absent for the class on {{3}}. 
If this is an error, please contact the admin desk.
```

**Name:** `leave_decision`
**Category:** UTILITY
**Language:** en
**Body:**
```
Dear {{1}},

The leave request for {{2}} from {{3}} to {{4}} has been {{5}}.
```

**Name:** `fee_invoice_issued`
**Category:** UTILITY
**Language:** en
**Body:**
```
Dear {{1}},

A new fee invoice ({{2}}) has been generated for {{3}}.
Amount Due: ₹{{4}}
Due Date: {{5}}
```
*Button (URL):* Pay Now `https://{domain}/portal/student/dues`

**Name:** `fee_due_reminder`
**Category:** UTILITY
**Language:** en
**Body:**
```
Dear {{1}},

This is a reminder that the fee invoice ({{2}}) for {{3}} is due on {{4}}.
Pending Amount: ₹{{5}}
```
*Button (URL):* Pay Now `https://{domain}/portal/student/dues`

**Name:** `fee_overdue`
**Category:** UTILITY
**Language:** en
**Body:**
```
Dear {{1}},

The fee invoice ({{2}}) for {{3}} is now OVERDUE.
Pending Amount: ₹{{4}}
Late fees may apply if not paid promptly.
```
*Button (URL):* Pay Now `https://{domain}/portal/student/dues`

**Name:** `payment_receipt`
**Category:** UTILITY
**Language:** en
**Body:**
```
Dear {{1}},

We have received your payment of ₹{{2}} for {{3}}.
Receipt Number: {{4}}.

Thank you!
```
*Button (URL):* Download Receipt `https://{domain}/api/v1/fees/receipts/{{5}}/download`

**Name:** `payment_failed`
**Category:** UTILITY
**Language:** en
**Body:**
```
Dear {{1}},

Your recent payment attempt for ₹{{2}} failed.
Reason: {{3}}

Please try again using the portal.
```
*Button (URL):* Retry Payment `https://{domain}/portal/student/dues`

**Name:** `certificate_ready`
**Category:** UTILITY
**Language:** en
**Body:**
```
Dear {{1}},

Congratulations! The {{2}} certificate for {{3}} is now available.
```
*Button (URL):* View Certificate `https://{domain}/verify/{{4}}`

## 3. Marketing (Broadcasts & Announcements)
**Name:** `event_announcement`
**Category:** MARKETING
**Language:** en
**Body:**
```
Dear {{1}},

{{2}}

Join us for this exciting event! 
Reply STOP to unsubscribe from these announcements.
```
