# Demo Browser Observer Contract Notes

Verified: 2026-06-23

Official source: none. This is an internal fake source for control-plane testing only.

Implementation status: fake worker only. No browser automation, no external navigation, no HTML
capture, no screenshots, no cookies and no provider live calls.

Policy facts used by Flight Hunter:

- Disabled by default with `SCRAPING_OBSERVER_ENABLED=false`.
- User action is required for every observation.
- Background execution is forbidden.
- Permission attestation is required even for the demo source.
- Prohibited capabilities remain blocked: CAPTCHA solving, stealth/fingerprint evasion, proxy
  rotation, cookie reuse, credential reuse and access-control bypass.
- Results are labelled `live_observed` and still require manual confirmation before purchase.

Current Flight Hunter policy:

- Source id: `demo_browser`.
- Allowed domain in demo attestation: `flight-hunter.local`.
- Allowed capabilities: `public_navigation`, `public_dom_read`.
- Raw persistence: disabled.
- Normalized persistence: allowed only for observed demo offers.
- Real source onboarding requires a separate provider-contract file, sanitized fixtures, contract
  tests, security review and operational runbook.
