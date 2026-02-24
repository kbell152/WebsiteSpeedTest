# Latest Performance Test: https://aprilbell.com

## What Was Tested
- Site: https://aprilbell.com
- Strategy: mobile
- Run ID: 179
- Saved timestamp (UTC): 2026-02-24T22:19:46+00:00
- Lighthouse fetchTime (UTC): 2026-02-24T22:19:18.674Z
- Note: None

## Run Context
No extra run context was provided.
Tip: use `--context` or `--context-file` for host/plugin/Divi details.

## Results
- Performance Score: 60.0
- FCP: 4658.0 ms
- LCP: 6083.0 ms
- TBT: 150.0 ms
- CLS: 0.0806350892623821
- Speed Index: 6673.9 ms
- TTFB: 321.0 ms
- Warnings: 0
- Errors: 0

## Suggestions (Prioritized TODOs)
1. Time to Interactive | audit=interactive | priority=14137.0 | impact_ms=13257.0 | score=0.12
   - Time to Interactive is the amount of time it takes for the page to become fully interactive. [Learn more about the Time to Interactive metric](https://developer.chrome.com/docs/lighthouse/performance/interactive/).
2. Speed Index | audit=speed-index | priority=7313.9 | impact_ms=6673.9 | score=0.36
   - Speed Index shows how quickly the contents of a page are visibly populated. [Learn more about the Speed Index metric](https://developer.chrome.com/docs/lighthouse/performance/speed-index/).
3. Largest Contentful Paint | audit=largest-contentful-paint | priority=6963.0 | impact_ms=6083.0 | score=0.12
   - Largest Contentful Paint marks the time at which the largest text or image is painted. [Learn more about the Largest Contentful Paint metric](https://developer.chrome.com/docs/lighthouse/performance/lighthouse-largest-contentful-paint/)
4. First Contentful Paint | audit=first-contentful-paint | priority=5528.0 | impact_ms=4658.0 | score=0.13
   - First Contentful Paint marks the time at which the first text or image is painted. [Learn more about the First Contentful Paint metric](https://developer.chrome.com/docs/lighthouse/performance/first-contentful-paint/).
5. Minimize main-thread work | audit=mainthread-work-breakdown | priority=3138.7 | impact_ms=2138.7 | score=0.0
   - Consider reducing the time spent parsing, compiling and executing JS. You may find delivering smaller JS payloads helps with this. [Learn how to minimize main-thread work](https://developer.chrome.com/docs/lighthouse/performance/mainthread-work-breakdown/)
6. Reduce unused CSS | audit=unused-css-rules | priority=1300.0 | impact_ms=300.0 | score=0.0
   - Reduce unused rules from stylesheets and defer CSS not used for above-the-fold content to decrease bytes consumed by network activity. [Learn how to reduce unused CSS](https://developer.chrome.com/docs/lighthouse/performance/unused-css-rules/).
7. Links are not crawlable | audit=crawlable-anchors | priority=1000.0 | impact_ms=0.0 | score=0.0
   - Search engines may use `href` attributes on links to crawl websites. Ensure that the `href` attribute of anchor elements links to an appropriate destination, so more pages of the site can be discovered. [Learn how to make links crawlable](https://support.google.com/webmasters/answer/9112205)
8. Forced reflow | audit=forced-reflow-insight | priority=1000.0 | impact_ms=0.0 | score=0.0
   - A forced reflow occurs when JavaScript queries geometric properties (such as offsetWidth) after styles have been invalidated by a change to the DOM state. This can result in poor performance. Learn more about [forced reflows](https://developer.chrome.com/docs/performance/insights/forced-reflow) and possible mitigations.
9. Background and foreground colors do not have a sufficient contrast ratio. | audit=color-contrast | priority=1000.0 | impact_ms=0.0 | score=0.0
   - Low-contrast text is difficult or impossible for many users to read. [Learn how to provide sufficient color contrast](https://dequeuniversity.com/rules/axe/4.11/color-contrast).
10. Font display | audit=font-display-insight | priority=1000.0 | impact_ms=0.0 | score=0.0
   - Consider setting [font-display](https://developer.chrome.com/docs/performance/insights/font-display) to swap or optional to ensure text is consistently visible. swap can be further optimized to mitigate layout shifts with [font metric overrides](https://developer.chrome.com/blog/font-fallbacks).
11. Network dependency tree | audit=network-dependency-tree-insight | priority=1000.0 | impact_ms=0.0 | score=0.0
   - [Avoid chaining critical requests](https://developer.chrome.com/docs/performance/insights/network-dependency-tree) by reducing the length of chains, reducing the download size of resources, or deferring the download of unnecessary resources to improve page load.
12. Document does not have a meta description | audit=meta-description | priority=1000.0 | impact_ms=0.0 | score=0.0
   - Meta descriptions may be included in search results to concisely summarize page content. [Learn more about the meta description](https://developer.chrome.com/docs/lighthouse/seo/meta-description/).
13. `[user-scalable="no"]` is used in the `<meta name="viewport">` element or the `[maximum-scale]` attribute is less than 5. | audit=meta-viewport | priority=1000.0 | impact_ms=0.0 | score=0.0
   - Disabling zooming is problematic for users with low vision who rely on screen magnification to properly see the contents of a web page. [Learn more about the viewport meta tag](https://dequeuniversity.com/rules/axe/4.11/meta-viewport).
14. Document does not have a main landmark. | audit=landmark-one-main | priority=1000.0 | impact_ms=0.0 | score=0.0
   - One main landmark helps screen reader users navigate a web page. [Learn more about landmarks](https://dequeuniversity.com/rules/axe/4.11/landmark-one-main).
15. Render blocking requests | audit=render-blocking-insight | priority=1000.0 | impact_ms=0.0 | score=0.0
   - Requests are blocking the page's initial render, which may delay LCP. [Deferring or inlining](https://developer.chrome.com/docs/performance/insights/render-blocking) can move these network requests out of the critical path.
16. Heading elements are not in a sequentially-descending order | audit=heading-order | priority=1000.0 | impact_ms=0.0 | score=0.0
   - Properly ordered headings that do not skip levels convey the semantic structure of the page, making it easier to navigate and understand when using assistive technologies. [Learn more about heading order](https://dequeuniversity.com/rules/axe/4.11/heading-order).
17. Uses third-party cookies | audit=third-party-cookies | priority=1000.0 | impact_ms=0.0 | score=0.0
   - Third-party cookies may be blocked in some contexts. [Learn more about preparing for third-party cookie restrictions](https://privacysandbox.google.com/cookies/prepare/overview).
18. Issues were logged in the `Issues` panel in Chrome Devtools | audit=inspector-issues | priority=1000.0 | impact_ms=0.0 | score=0.0
   - Issues logged to the `Issues` panel in Chrome Devtools indicate unresolved problems. They can come from network request failures, insufficient security controls, and other browser concerns. Open up the Issues panel in Chrome DevTools for more details on each issue.
19. Links do not have a discernible name | audit=link-name | priority=1000.0 | impact_ms=0.0 | score=0.0
   - Link text (and alternate text for images, when used as links) that is discernible, unique, and focusable improves the navigation experience for screen reader users. [Learn how to make links accessible](https://dequeuniversity.com/rules/axe/4.11/link-name).
20. Minify JavaScript | audit=unminified-javascript | priority=500.0 | impact_ms=0.0 | score=0.5
   - Minifying JavaScript files can reduce payload sizes and script parse time. [Learn how to minify JavaScript](https://developer.chrome.com/docs/lighthouse/performance/unminified-javascript/).
21. Reduce unused JavaScript | audit=unused-javascript | priority=500.0 | impact_ms=0.0 | score=0.5
   - Reduce unused JavaScript and defer loading scripts until they are required to decrease bytes consumed by network activity. [Learn how to reduce unused JavaScript](https://developer.chrome.com/docs/lighthouse/performance/unused-javascript/).
22. Use efficient cache lifetimes | audit=cache-insight | priority=500.0 | impact_ms=0.0 | score=0.5
   - A long cache lifetime can speed up repeat visits to your page. [Learn more about caching](https://developer.chrome.com/docs/performance/insights/cache).
23. Improve image delivery | audit=image-delivery-insight | priority=500.0 | impact_ms=0.0 | score=0.5
   - Reducing the download time of images can improve the perceived load time of the page and LCP. [Learn more about optimizing image size](https://developer.chrome.com/docs/performance/insights/image-delivery)
24. Host/cache configuration review | audit=host-cache-check | priority=450.0 | impact_ms=0.0 | score=0.0
   - No edge cache status header detected (host/CDN dependent).
25. Initial server response time was short | audit=server-response-time | priority=221.0 | impact_ms=221.0 | score=1.0
   - Keep the server response time for the main document short because all other requests depend on it. [Learn more about the Time to First Byte metric](https://developer.chrome.com/docs/lighthouse/performance/time-to-first-byte/).

## Host/Cache Notes
- No edge cache status header detected (host/CDN dependent).

## LCP Deep Dive
- LCP element snippet: n/a
- LCP resource URL: n/a
- LCP phase TTFB: n/a ms
- LCP phase load delay: n/a ms
- LCP phase load time: n/a ms
- LCP phase render delay: n/a ms

## Full Raw Data
- Full JSON for this test: `LH_Reports_For_Chat/latest-test.json`
- This file is overwritten automatically by the next successful `run`.