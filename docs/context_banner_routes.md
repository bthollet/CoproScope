# Context banner route integration

`base.html` already renders `_context_banner.html` when a page context provides a
non-empty `context_banner`. The route layer now supplies that value from
`build_context_banner` for the main operational pages only:

- cockpit `/`
- actions `/actions`
- documents `/documents` and document detail pages
- atelier pieces `/pieces`
- depot local `/depot`
- gouvernance `/gouvernance`
- demandes `/demandes`
- pilotage `/pilotage`

The integration stays in `server/src/coproscope/web/app.py`: no template,
style, or dashboard viewmodel refactor is required. Pages outside this list keep
the previous contract and render without a banner unless a caller explicitly
passes one.

Routes continue to render when no signed coffre is configured. In that case
`build_context_banner` returns a review-state banner explaining that the coffre
signe and sync folder still need to be declared.

When the local UI token is enabled and present on the request, the banner's next
action link keeps the token by using the existing route URL helper. This avoids a
token drop when moving from a protected page toward `/gouvernance`.

Minimal coverage lives in `server/tests/test_ui_context_banner_routes.py` and
checks:

- the listed main pages render a banner on the synthetic instance without signed coffre
  settings;
- the next action link preserves `?token=...`;
- a non-main page keeps rendering without a banner.
