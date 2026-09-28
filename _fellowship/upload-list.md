# قائمة الرفع

الوجهة: `https://github.com/Meyar-Platform/Meyar/upload/main` ، كل ملف بمساره داخل المستودع كما هو في `publish_paused/`.
المقارنة مع جذر المستودع في الفرع الرئيسي كما كان عند بدء العمل. ملف `CNAME` لا يُمس.

## ملفات تُستبدل (6)

| المسار في المستودع | md5 |
|---|---|
| `404.html` | `bc6cbd6e2fdcb45917983536fe6ed787` |
| `index.html` | `2ca36618b7ec75d8000e6b88edfc83d8` |
| `manifest.webmanifest` | `613d76b81f1ae000dbf4d6fba5165e5f` |
| `private-sector.html` | `c1a0c66993836dd6c883cba7d411535a` |
| `sitemap.xml` | `6b30a7ae254a3126556fada1d5bf3bbb` |
| `sw.js` | `326f821429b5a176b7d46530218d53f9` |

## ملفات جديدة (9)

| المسار في المستودع | md5 |
|---|---|
| `access.js` | `1867e3943812abfd2f1cd5cac44d66d2` |
| `business-environment.html` | `705534d68e3e388e851d5f1557224840` |
| `capital-structure.html` | `405094cf46dfbffca27a76cd4bb21e99` |
| `data/bizenv-outline.json` | `9ec462528dbdfb6a41f1f37c2dd489f2` |
| `data/bizenv-questions.json` | `05cb5cb2234a9df6ee3e99122f0ab7f4` |
| `data/bizenv-summaries.json` | `d6e606c4c4d7b7d6e60c51521f39baf3` |
| `data/fellowship-subjects.json` | `49be52775cba53c58b5a6258b42fdbe9` |
| `fellowship.html` | `4fba5744db6adec9687c604d6add39ec` |
| `public-sector.html` | `9c60b8db09d3576718af849dd744abd0` |

## ملفات لم تتغير، لا حاجة لرفعها (15)

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
`robots.txt`

ترتيب مقترح للرفع: ملفات `data/` و`access.js` أولاً، ثم الصفحات، ثم `sw.js` و`sitemap.xml` آخراً، حتى لا يخزّن عامل الخدمة الجديد نسخة ناقصة.
