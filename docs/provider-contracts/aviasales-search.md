# Aviasales Search API Contract Notes

Verified: 2026-06-23

Official sources:

- https://support.travelpayouts.com/hc/en-us/articles/30565016140434-Aviasales-Flight-Search-API-real-time-and-multi-city-search
- https://support.travelpayouts.com/hc/en-us/articles/210995808-How-to-get-access-to-the-Aviasales-Search-API
- https://support.travelpayouts.com/hc/en-us/articles/34788165535250-Search-API-usage-rules
- https://support.travelpayouts.com/hc/en-us/articles/203956173-Aviasales-Flights-Search-API-old-version

Implementation status: policy skeleton only. No Search API HTTP client is implemented in the current slice.

Policy facts used by Flight Hunter:

- Access is only for projects with confirmed 50,000+ MAU.
- The new Flight Search API version is available from November 1, 2025.
- The old API version stops working on June 15, 2026 and must not be used for new work.
- Search requests must be initiated by a real user action.
- Search results must be shown to the user and must not be automatically collected.
- Results must not be combined with APIs from other flight metasearch services.
- Booking links may be generated only after the user clicks the booking action.
- API requests must be sent server-side; client-side calls are not supported.

Current Flight Hunter policy:

- Adapter disabled by default.
- `credentials_present=false` and `access_approved=false` until explicitly configured.
- `background_requests_allowed=false`.
- `user_action_required=true`.
- `merge_with_other_sources_allowed=false`, so `merge_scope=PROVIDER_ISOLATED`.
- `booking_link_requires_click=true` and `preload_booking_links_allowed=false`.
