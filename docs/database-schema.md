# Trust Africa Database Schema

## Users

Stores information about platform members.

Fields:

- id
- name
- country
- reputation_level
- successful_trades

---

## Agreements

Stores protected trade agreements.

Fields:

- id
- buyer
- seller
- product
- amount
- delivery_date
- status

---

## Evidence

Stores uploaded evidence.

Fields:

- id
- agreement_id
- type
- file_reference
- upload_time

---

## AI Reviews

Stores AI reasoning.

Fields:

- id
- agreement_id
- confidence_score
- reasoning
- recommendation

---

## Human Validator Reviews

Stores validator decisions.

Fields:

- id
- agreement_id
- validator_name
- decision
- notes

---

## Reputation

Tracks honest cooperation.

Fields:

- user_id
- successful_trades
- disputes
- trust_level