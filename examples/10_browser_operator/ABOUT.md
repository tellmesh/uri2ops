---
landing:
  cards:
    - id: browser-op-connector
      layout: connector
      order: 40
      logo: BR
      docs: docs/examples.html#ex-10_browser_operator
      i18n:
        pl:
          tag: Browser
          title: Operator przeglądarki (mock + real)
          lead: browser://chrome/page/open + screen://... — automatyzacja UI z policy approval.
        en:
          tag: Browser
          title: Browser operator (mock + real)
          lead: browser://chrome/page/open + screen://... — UI automation with policy approval.
        de:
          tag: Browser
          title: Browser-Operator (Mock + Real)
          lead: browser://chrome/page/open + screen://... — UI-Automatisierung mit Policy-Genehmigung.
      snippet: |
        NL: "otwórz stronę i zrób screenshot"
        URI: browser://chrome/page/open + screen://browser/active/screenshot
        Run: urish run ... --adapter mock

    - id: browser-op-card
      layout: card
      order: 50
      docs: docs/examples.html#ex-10_browser_operator
      i18n:
        pl:
          tag: UI
          title: browser + screen operator
        en:
          tag: UI
          title: browser + screen operator
        de:
          tag: UI
          title: browser + screen operator
      snippet: |
        urish call 'browser://chrome/page/open' --payload '{"url":"..."}'
        urish call 'screen://browser/active/screenshot'
---
<ul>
<li>Mock dla testów, real Playwright dla prawdziwych PNG.</li>
<li>Polityka: approve dla side-effects (otwieranie stron).</li>
<li>Artefakty w output/artifacts/operator/ — audytowalne z file://.</li>
</ul>
