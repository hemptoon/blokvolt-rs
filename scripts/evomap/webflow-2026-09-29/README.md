# The Evolako map page code before 06.10.2026 (rollback copy)

`head.html` and `footer.html` are the head and footer custom code of the Webflow page `/mapa-punjaca`
(page `6abaf73484f6a5d61585b9e5`) as read with `get_page_freeform_code` on 06.10.2026, before the footer's inline map
script (29.09.2026, 46 793 characters) was replaced by the tag of the hosted script (`static/assets/embed/evomap-*.js`).
The inline script works with the current map data (checked on 06.10.2026 with the `guard` prices and `tx.json`), so
writing these two blocks back with `set_page_freeform_code` and publishing restores the old map. The head was not
changed on 06.10.2026: its `<style>` block (29.09.2026) and `window.EVM_TX` stay, and the hosted script adds its own
styles (`<style id="evm-css">`).
