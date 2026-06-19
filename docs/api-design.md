# Trust Africa API Design

## Purpose

The backend connects the frontend, AI engine, database, escrow system, and GenLayer intelligent contract.

---

## Core API Endpoints

### 1. Create Agreement

POST /api/agreements

Creates a new protected trade agreement.

Fields:

- buyer
- seller
- product
- amount
- deliveryDate
- evidenceRequired

---

### 2. Review Agreement

POST /api/agreements/review

Sends the agreement to the Trust Guide for clarity review.

Checks:

- Is the product clear?
- Is the amount clear?
- Is the delivery date clear?
- Is evidence required?

---

### 3. Deposit Escrow

POST /api/escrow/deposit

Locks USDC after both parties accept the agreement.

---

### 4. Upload Evidence

POST /api/evidence

Uploads proof such as:

- Receipt
- Tracking number
- Photos
- Delivery confirmation

---

### 5. AI Review

POST /api/review/ai

AI reviews the evidence and returns:

- reasoning
- confidence score
- suggested decision

---

### 6. Human Validator Review

POST /api/review/validator

Used when AI confidence is low.

Validator can choose:

- approve release
- refund buyer
- request more evidence

---

### 7. Final Decision

POST /api/decision

Records the final decision and updates agreement status.

---

## Agreement Statuses

- AGREEMENT_CREATED
- AGREEMENT_REVIEWED
- ACCEPTED_BY_BOTH
- ESCROW_FUNDED
- EVIDENCE_SUBMITTED
- AI_REVIEW_COMPLETE
- HUMAN_REVIEW_REQUIRED
- RELEASED
- REFUNDED
- CLOSED