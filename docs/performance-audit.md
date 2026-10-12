# Mobile performance audit — 2026-10-12

Baseline: `cbe3a72a3c55df75ffbe99014ab7620f3ead45d5` (main). This is a static Webflow export: 52 HTML documents, three shared CSS files, an 816,995-byte shared JavaScript runtime, and no build/lint scripts. No production changes or redesign are included.

## Findings and changes

- **Fonts, all 52 HTML documents:** replaced the parser-blocking WebFont.js script and its inline call with one Google Fonts CSS2 stylesheet using `display=swap`. Removed body-level Poppins and duplicate Montserrat imports where present. Kept existing preconnects, Montserrat normal/italic weights 300–800, and Poppins 400 (including the existing browser-synthesized bold treatment). Weights 100, 200 and 900 are not referenced in the inspected CSS/HTML. No Bunny Fonts or Roboto files/declarations were found in the repository. Fonts used inside third-party frames are outside this patch. No runtime or CSS references to WebFont or its font-state classes were found.
- **`css/components.css`:** added `font-display: swap` to the sole local `@font-face`, an embedded Webflow icon font. Its original data URL remains intact.
- **Homepage LCP (`index.html`, `css/ellehomme.css`):** the locally observed LCP was `.header83_background-images`, using `Untitled_design_5.jpg`, not the later `IMG_9085.jpg`. Replaced that CSS background with a decorative, absolutely positioned image inside the same wrapper. `object-fit: cover`, `object-position: 0 0`, the overlay, sticky positioning, wrapper height and all content remain unchanged. The eager image has high fetch priority and exactly one matching responsive preload.
- **`images/home-hero-{800,1200,1600,2000}.webp`:** generated from the same 2000×1100 original at WebP quality 90; no recropping. Responsive sizes account for *cover height*, not just viewport width, to avoid a blurry portrait crop. Originals remain available and untouched. Measured PSNR against equivalently resized originals was 43.3–45.4 dB; this is not a substitute for real-device visual approval.
- **Contact and landing-page hero images:** existing `.header65_background-image` and `.header69_background-image` remain eager, receive high fetch priority, and get actual raster dimensions. Already-discoverable HTML heroes are not additionally preloaded. Placeholder SVGs keep their intrinsic sizing.
- **Below-the-fold content images:** `.header36_image` and `.header37_image` after the hero now use native lazy loading and actual dimensions, including replacing invalid `width="Auto"`. Existing assets, srcsets, sizes, classes and styling remain unchanged. The services page's potentially visible first content image remains eager; the style guide is not subjected to content-image loading changes.

### Measured byte savings, not a PageSpeed score

The original homepage background is **174,338 bytes**. New variants:

| Width | Bytes | Reduction vs original |
| --- | ---: | ---: |
| 800 | 30,590 | 82.5% |
| 1200 | 66,892 | 61.6% |
| 1600 | 107,228 | 38.5% |
| 2000 | 151,330 | 13.2% |

At 390×844, DPR 1, the local browser selected the 1600 variant; at 1440×900 it selected 2000. High-DPR phones can select 2000 because the image must cover a tall viewport. The preload and image selected the same resource without duplicate hero requests in the representative probes.

### JavaScript, CSS and integrations deliberately retained

- GTM is already asynchronous. Its bootstrap, container, data layer, noscript iframe and timing are unchanged. Delaying it could lose early events.
- LeadConnector chat loader, form iframe attributes and all form embed scripts remain byte-for-byte unchanged. Several pages include the form embed script twice. Removing or deferring it without exercising the vendor behavior could break multi-form sizing/listeners, so no such change is included.
- jQuery 3.5.1 and the exported runtime are retained in their original order and timing. The runtime directly requires jQuery and owns navigation, dropdowns, sliders, forms and Webflow interactions. Removing modules from the generated bundle is not justified by this audit. Removing WebFont.js is the verified JavaScript reduction; **TBT reduction has not been measured**.
- Shared layout CSS remains render-blocking deliberately: async-loading or speculative pruning can cause flashes and break runtime-generated states or other HTML pages.
- Vercel Speed Insights initialization and `/_vercel/speed-insights/script.js` remain byte-for-byte unchanged on every page. Live collection still requires preview/production verification.
- Metadata, titles, canonical links, copy, navigation links, booking links, inputs, forms, iframes, and non-font integration scripts are protected by the baseline preservation test.

## Validation and limitations

Commands:

```sh
npm ci
node --check js/ellehomme.js
python3 tests/performance_audit.py
python3 tests/performance_audit.py --baseline cbe3a72
git diff --check
```

Static checks pass on all 52 pages: one swap-enabled font stylesheet, no WebFont/import duplication, no missing local links/src/srcset resources, eager prioritized heroes, matched responsive preload, and preserved content/integrations against the baseline. Dependency installation passes with no reported vulnerabilities. No project build/lint command exists.

Representative local Chromium probes covered homepage, contact, Botox, laser hair removal and about-us at 390×844 and 1440×900, DPR 1. Modified pages had no JavaScript exceptions in these probes. External fonts, GTM, chat and form requests were blocked; jQuery was supplied locally at the original version; Speed Insights was stubbed. Baseline's `WebFont is not defined` exception is an artifact of that blocked external loader, not a claim about production. Thus these tests cannot establish live font metrics, analytics events, chat/form success, Speed Insights delivery, real-world CLS, or a production performance score.

The all-page Chromium sweep also loaded all 52 pages at both widths (104 baseline/modified comparisons) with no modified-page JavaScript exceptions under those same external-request limitations. Initial full-document geometry comparisons showed subpixel differences in distant content after lazy-image placeholders; a focused follow-up on homepage, Botox and manicures found deltas of 0.14–0.28 CSS pixels, and their mobile menus opened successfully in both versions after animation completion. A follow-up mobile sweep opened menus successfully on all applicable pages and had no modified-page exceptions. Its geometry check was within one CSS pixel on 51/52 pages; one thin-lips sample reported a larger delta, but a focused rerun returned only a 0.28-pixel distant-content difference and no desktop difference. The transient sample was not reproduced; thin-lips should receive particular attention in manual scroll/layout testing. These are not live integration tests.

Representative screenshot comparisons were pixel-identical on contact and about-us at both widths, and on treatment pages at desktop width. Mobile treatment differences were small animation-timing differences; homepage differences reflect WebP compression/resizing, with mean channel differences below 0.32/255 in those captures. Real-device visual review remains necessary.

No Google PageSpeed Insights score improvement, field Core Web Vitals improvement, or mobile TBT improvement is claimed. Local unthrottled LCP timings are not comparable to PSI and are intentionally not presented as performance results.

## Manual acceptance checklist before merge

1. Run mobile PSI/Lighthouse at least three times on the unchanged production site and the PR preview using the same settings; compare median LCP, TBT, CLS and the actual LCP element. Do not merge solely on one score.
2. Compare homepage hero crop, text/typography and all landing-page heroes on portrait/landscape mobile, high-DPR devices, tablet and desktop. Check slow-font loading for layout shift and duplicate requests.
3. Test mobile navigation, dropdowns, sliders, scrolling interactions, booking links, password/error pages and contact links. Scroll the entire page to confirm lazy images render and reserve space correctly.
4. Exercise every LeadConnector form, including pages with multiple forms: sizing, submission, success/error and attribution. Open chat and send a test message.
5. Verify GTM events in Tag Assistant and Vercel Speed Insights network delivery (`/_vercel/speed-insights/script.js` plus collection requests), and confirm incoming samples in the project dashboard after deployment.
6. Check the preview console/network for failed assets, font CSS errors, integration failures and duplicate preload requests.
7. Only after evidence from those checks, consider a separate, consent-aware third-party scheduling or runtime-reduction change. The large Webflow runtime remains the main unaddressed JavaScript opportunity.

## File-by-file review

All HTML files below receive the shared font fix. **H** = eager high-priority hero with dimensions where raster; **L** = below-fold image lazy loading/dimensions. No unlisted HTML behavior changes are allowed by the preservation test.

| HTML file | Additional change |
| --- | --- |
| `401.html` | font fix only |
| `404.html` | font fix only |
| `contact.html` | H |
| `index.html` | responsive WebP LCP + matched preload, L (4 images) |
| `pages/about-us.html` | font fix only |
| `pages/acne-scars-chicago.html` | H, L (1 images) |
| `pages/airbrush-tanning-chicago.html` | H, L (3 images) |
| `pages/aviclear-acne-laser-chicago.html` | H, L (3 images) |
| `pages/beauty.html` | H, L (1 images) |
| `pages/bellafill-chicago.html` | H, L (3 images) |
| `pages/belotero-chicago.html` | H, L (3 images) |
| `pages/botox-chicago.html` | H, L (3 images) |
| `pages/chemical-peels-chicago.html` | H, L (3 images) |
| `pages/colombian-body-sculpting-wood-therapy-massage-chicago.html` | H, L (3 images) |
| `pages/dermal-filler.html` | H, L (1 images) |
| `pages/drainage-massage-chicago.html` | H, L (3 images) |
| `pages/dysport-chicago.html` | H, L (3 images) |
| `pages/electrolysis-pcos-chicago.html` | H, L (3 images) |
| `pages/ellexclusive-chicago.html` | H, L (1 images) |
| `pages/emsculpt-neo-chicago.html` | H, L (3 images) |
| `pages/hair-chicago.html` | H, L (2 images) |
| `pages/intimacy-shot-for-women-chicago.html` | H, L (3 images) |
| `pages/ipl-photofacial-chicago.html` | H, L (3 images) |
| `pages/iv-therapy-chicago.html` | H, L (3 images) |
| `pages/juvederm-chicago.html` | H, L (3 images) |
| `pages/kybella-chicago.html` | H, L (3 images) |
| `pages/laser-hair-removal-chicago.html` | H, L (3 images) |
| `pages/laser-therapy-chicago.html` | H, L (1 images) |
| `pages/manicures-chicago.html` | H, L (2 images) |
| `pages/microneedling-chicago.html` | H, L (3 images) |
| `pages/morpheus8-chicago.html` | H, L (3 images) |
| `pages/performance-shot-chicago.html` | H, L (3 images) |
| `pages/post-operative-massage-chicago.html` | H, L (3 images) |
| `pages/privacy-policy.html` | font fix only |
| `pages/prp-hairloss-chicago.html` | H, L (3 images) |
| `pages/prp.html` | H, L (1 images) |
| `pages/radiesse-filler.html` | H, L (3 images) |
| `pages/restylane-chicago.html` | H, L (3 images) |
| `pages/revanesse-chicago.html` | H, L (3 images) |
| `pages/sculptra-chicago.html` | H, L (3 images) |
| `pages/services.html` | font fix only |
| `pages/skin.html` | H, L (1 images) |
| `pages/spider-veins-chicago.html` | H, L (3 images) |
| `pages/terms-and-conditions.html` | font fix only |
| `pages/thin-lips-chicago.html` | H, L (3 images) |
| `pages/treatment-category-page.html` | H, L (1 images) |
| `pages/treatment-page.html` | H, L (3 images) |
| `pages/votiva-chicago.html` | H, L (3 images) |
| `pages/waxing-chicago.html` | H, L (2 images) |
| `pages/wrinkle-relaxers-chicago.html` | H, L (1 images) |
| `pages/xeomin-chicago.html` | H, L (3 images) |
| `style-guide-6a3924ad-5594-4820-9721-af15aaba79fb.html` | font fix only |

The two changed CSS files and four new image files are explained above. `tests/performance_audit.py` adds dependency-free resource/loading and baseline-preservation regression checks. `docs/performance-audit.md` records findings, measurements, deferred risks and the acceptance checklist. Package files, the JavaScript runtime, SEO configuration and integration code are unchanged.
