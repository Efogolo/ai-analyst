# users

Grain (a guess from the data, confirm it): one row per user_id. 31,165 rows.

## Columns

| Name | Type | Null rate | Distinct |
| --- | --- | --- | --- |
| user_id | int64 | 0.00% | 31,165 |
| signup_date | datetime64[ns] | 0.00% | 12,512 |
| country | object | 0.00% | 4 |
| device_type | object | 0.00% | 3 |

## Date ranges

- `signup_date`: 2022-01-01T00:00:00 to 2026-09-24T22:59:05

## Low-cardinality values

- `country`: US (12,472), Rest (6,270), India (6,238), EU (6,185)
- `device_type`: Web (10,466), Android (10,363), iOS (10,336)

## Meaning

- `user_id`: key (inferred).
- `signup_date`: account creation (inferred). Spike in September 2025 (quirk: September 2025 spike).
- `country`: US, EU, India or Rest (inferred).
- `device_type`: Web, Android or iOS (inferred).

Grain (inferred): one row per user. 31,165 users against 30,747 subscriptions, so some users have no subscription row (inferred).
