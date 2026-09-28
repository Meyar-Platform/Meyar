# قائمة الرفع

الوجهة: `https://github.com/Meyar-Platform/Meyar/upload/main` ، كل ملف بمساره داخل المستودع كما هو في `publish_paused/`.
المقارنة مع جذر المستودع في الفرع الرئيسي كما كان عند بدء العمل. ملف `CNAME` لا يُمس.

## ملفات تُستبدل (4)

| المسار في المستودع | md5 |
|---|---|
| `index.html` | `963838754cce18c215b27b3b722d3039` |
| `private-sector.html` | `c1a0c66993836dd6c883cba7d411535a` |
| `sitemap.xml` | `6b30a7ae254a3126556fada1d5bf3bbb` |
| `sw.js` | `0e369bd820ee66c3878b76b833bd3d6e` |

## ملفات جديدة (9)

| المسار في المستودع | md5 |
|---|---|
| `access.js` | `1867e3943812abfd2f1cd5cac44d66d2` |
| `business-environment.html` | `ace9f2f4bffc2234912eb25ce292cc4b` |
| `capital-structure.html` | `405094cf46dfbffca27a76cd4bb21e99` |
| `data/bizenv-outline.json` | `b635d68c9f76bb33a1d57e751462c396` |
| `data/bizenv-questions.json` | `6e91f0c9962b044520fa9f9db23008f5` |
| `data/bizenv-summaries.json` | `ba28ac68cffb4686908d932ad9e29b14` |
| `data/fellowship-subjects.json` | `8fcf8290d85975bbaee60a04bdd429fb` |
| `fellowship.html` | `4fba5744db6adec9687c604d6add39ec` |
| `public-sector.html` | `9c60b8db09d3576718af849dd744abd0` |

## ملفات لم تتغير، لا حاجة لرفعها (17)

`404.html`
`CNAME`
`assets/logo-white.svg`
`assets/logo.svg`
`assets/share.jpg`
`fonts/tajawal-arabic-400-normal.woff2`
`fonts/tajawal-arabic-500-normal.woff2`
`fonts/tajawal-arabic-700-normal.woff2`
`fonts/tajawal-latin-400-normal.woff2`
`fonts/tajawal-latin-500-normal.woff2`
`fonts/tajawal-latin-700-normal.woff2`
`icons/apple-touch-icon.png`
`icons/icon-192.png`
`icons/icon-512.png`
`icons/icon-maskable-512.png`
`manifest.webmanifest`
`robots.txt`

ترتيب مقترح للرفع: ملفات `data/` و`access.js` أولاً، ثم الصفحات، ثم `sw.js` و`sitemap.xml` آخراً، حتى لا يخزّن عامل الخدمة الجديد نسخة ناقصة.
