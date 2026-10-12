# Production startup investigation and conservative form scheduling

Baseline: merged PR #7, commit `61a4222`. No Lighthouse score or speed improvement has been measured or claimed.

## Exact locations and dependencies

On the baseline homepage, the VIP iframe (`inline-rsssEcgmWCPzGVS0JZVa`) begins at line 627, followed by `form_embed.js` at 645. The footer iframe (`inline-roREHpypb8bsGL5YdAMg`) begins at 960, followed by that script at 979. Both are far below the viewport-height homepage hero. Contact has its own iframe (`inline-Q0w9VHISzh5hTvsLtWg3`) and the shared footer iframe. Vendor attributes identify each form and connect the iframe to its embed integration; all remain intact.

Across 49 pages there are 93 VIP/footer iframes and 94 form-embed script tags. The scripts are external classic scripts without async/defer in the baseline, so HTML parsing waits for each load/execution. A cached download can still execute twice. The markup does not prove that the second execution is redundant: vendor code might initialize individual frames, rewrite URLs for attribution, or attach sizing/submission listeners. We retain every vendor script occurrence rather than infer a safe deduplication contract from its identical URL.

The jQuery script precedes `js/ellehomme.js` at the end of each document. The exported runtime reads `window.jQuery`, registers navigation/dropdown/slider/forms/accessibility/scroll modules, and immediately initializes `ix2` with the site's interaction configuration. Existing `data-w-id` elements and navigation events rely on it. Its uncompressed size is 816,995 bytes; a local compressed estimate is about 76 KB, not a measured network transfer. Bundle size alone does not establish execution cost. We found no source build pipeline permitting safe module-level tree shaking. Do not remove the interaction engine or defer the whole runtime until interaction: that could change initial styles and make navigation unavailable.

GTM's bootstrap is already async. The chat loader is a classic script at the end of the document, with a widget ID and resource URL. Its initialization contract and downstream resources cannot be verified from repository code. A timer/idle gate could delay availability or lose vendor events; we do not add one without vendor testing. GTM, chat, booking URLs, Webflow scripts and Speed Insights are untouched.

Shared render-blocking CSS totals approximately 212 KB uncompressed (about 28 KB using local compression estimates). It includes responsive layouts, Webflow states and interaction styles. Removing apparently unused selectors without all-page/runtime-state coverage would risk design and functionality. Neither async CSS nor speculative pruning is included.

## Implemented changes

- Add native `loading="lazy"` to the 93 clearly below-fold VIP/footer iframes across 49 pages. Original `src`, IDs, sizing styles, titles, data attributes and markup order remain unchanged. Browser-native loading keeps normal eager fallback in older browsers, requires no custom loader, and avoids replacing iframe URLs or altering attribution parameters.
- Add `defer` to all 94 vendor form scripts. Scripts can download while parsing continues and execute in original document order after the complete DOM exists. This moves execution out of parser-blocking positions; it does **not** remove vendor execution, postpone it until scroll, or establish a TBT reduction. Initial contact-form iframe loading remains unchanged.
- Add `tests/form_loading_audit.py` to compare all 52 HTML documents exactly against the merged baseline after normalizing only those two scheduling changes. It proves preservation of content, metadata, booking links, iframe attributes, script counts/order and other integrations.

Native lazy loading is heuristic, not an absolute promise of zero initial requests: frames close enough to the viewport still load early. This is intentionally less invasive than rewriting src/data-src and implementing a vendor-specific observer.

## Checks actually performed

- `python3 tests/form_loading_audit.py`: passes for 52 pages, 93 lazy frames and 94 deferred scripts; no other HTML changes.
- `python3 tests/performance_audit.py`: passes existing loading/local-resource checks on all 52 pages.
- `node --check js/ellehomme.js` and `git diff --check`: pass. Runtime and CSS are unchanged.
- Local mobile Chromium at 390×844: homepage and Botox initially requested neither form iframe, then requested both original iframe URLs after scrolling. Contact loaded both initially because native proximity loading allows it. Stubbed embed scripts ran at `document.readyState === 'interactive'` and saw both forms on each page.

Browser tests substituted inert form responses and a diagnostic embed script. They verify native scheduling, DOM availability and preservation, **not** vendor submission, sizing, attribution or chat behavior. Production URLs and vendor browser execution are unavailable in this sandbox. The actual vendor's compatibility with defer must be verified before merge. No live Lighthouse, network waterfall, TTFB, CPU coverage or TBT measurements are available; suspected bottlenecks remain hypotheses.

## Required manual acceptance before merge

1. On the PR preview, test VIP/footer forms on homepage and a treatment page after scrolling; submit, verify success/error behavior, dynamic height, received lead and UTM attribution. Test contact form immediately and footer after scroll. Inspect console and frame network errors.
2. Verify mobile layout/space reservation and no jumping when each form loads, including Safari and slow connections. Confirm vendor scripts do not depend on parser-time execution or `document.write`.
3. Confirm chat opens/sends, booking links work, GTM events arrive, navigation/interactions remain correct, and Speed Insights collects.
4. Run repeated mobile Lighthouse/PSI baseline and preview tests with identical settings. Record score, LCP, TBT, CLS, FCP, TTFB and third-party script execution costs. Do not interpret the local stub tests as a performance benchmark.
5. With the report/trace, verify whether one vendor embed execution handles both forms; only then deduplicate. Profile chat descendants and exported runtime long tasks before pursuing additional scheduling or module changes.

This PR deliberately implements a narrow verified scheduling change, not a claimed resolution of the reported 40/100 score. Duplicate-script removal, chat delays, runtime surgery and CSS pruning are deferred pending evidence, rather than shipped speculatively.
