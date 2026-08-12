# Security Policy

## Scope

This repository is a local-only Epic SMART on FHIR sandbox proof of concept. It is not designed or approved for production health-data processing.

## Reporting a vulnerability

Do not open a public issue containing credentials, OAuth authorization codes, access tokens, patient identifiers, screenshots with health data, or other PHI.

For this PoC, contact the repository owner privately through the contact method listed in the repository profile. If the application is ever deployed beyond local sandbox use, publish a dedicated security contact and incident-response process before accepting production data.

## Secret-handling requirements

Never commit `.env` files, client secrets, access tokens, refresh tokens, authorization codes, test-patient credentials, or FHIR responses containing patient data. If any is committed, revoke it where possible and remove it from Git history before making the repository public.
