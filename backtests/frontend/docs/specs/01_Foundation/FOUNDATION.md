# Foundation

## Source Anchors

- Source: src/main.tsx
- Source: src/global.css
- Source: src/index.css
- Source: src/layouts/ProLayout.tsx
- Source: package.json

## UI Baseline

- Stack: React 19 + React Router + Ant Design 5 + ProComponents
- Locale: Antd `zh_CN`
- Shell: ProLayout mixed admin layout with fixed header, fixed sidebar, and fluid content width
- Theme source:
  - ProLayout `navTheme="realDark"`
  - Ant Design default component theme
  - minimal project-local CSS overrides

## Tokens

### Colors

- No custom token file or theme object is defined in source.
- Effective visual colors are mostly Ant Design defaults plus a few local hard-coded values:
  - scrollbar track: `#f1f1f1`
  - scrollbar thumb: `#888`
  - scrollbar thumb hover: `#555`
  - simulator summary strip: `#1f1f1f`
  - agent log page background: `#141414`
  - agent log panel background: `#1e1e1e`
  - agent log panel text: `#d4d4d4`
  - helper gray text: `#999`

### Typography

- Active global font stack from `global.css`:
  - `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif, ...`
- Smoothing:
  - `-webkit-font-smoothing: antialiased`
  - `-moz-osx-font-smoothing: grayscale`
- Headings are mostly raw `h1` and Antd `Typography.Title`.

### Spacing

- Primary page padding: `20px`
- Repeated micro-spacing:
  - `8px` button gaps
  - `12px` to `16px` internal blocks
  - `16px` section margin bottoms

### Radius

- Local custom surfaces use soft radius:
  - scrollbar thumb: `4px`
  - config strip and log panel: `6px`
- Most component radius is inherited from Antd.

### Shadow

- No project-owned shadow scale found.

### Z-index

- No custom z-index system found.
- Overlays rely on Antd defaults.

### Motion

- No local motion tokens or animation patterns found.
- Interactions inherit Antd transitions and browser-native behavior.

## Global Styles

### Reset

- `* { margin: 0; padding: 0; box-sizing: border-box; }`

### Height Chain

- `html`, `body`, and `#root` are all `height: 100%`
- `.ant-layout` is forced to `min-height: 100vh`

### Body Defaults

- Body font is globally normalized
- No branded body background is set in active global CSS

### Scrollbars

- Thin custom WebKit scrollbar styling is applied globally

## Important Note On `src/index.css`

- `src/index.css` still contains default Vite starter dark/light theme CSS.
- The app entry imports `global.css`, not `index.css`.
- Treat `index.css` as legacy/non-canonical unless it is intentionally wired back in.

## Foundation Assessment

- This frontend is library-led rather than token-led.
- The real consistency comes from Antd/ProLayout defaults and repeated admin-page composition, not from a bespoke design system.
