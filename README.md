# Evan的试卷库 · 2018–2026 高考真题与平板演算工作台

> 纯公益免费 · 无文综/理综新高考真题库 · Apple 风格双栏刷题与平板级手写草稿纸 · 分层多解精讲

## 在线直接刷题（学生免安装）

- **官方公益在线地址**：https://mojuan-gaokao.pages.dev
- **平板 / 手机安装为全屏应用**：用 iPad Safari 或手机浏览器打开上面网址 → 点击 **「添加到主屏幕」**，即可获得无浏览器边框的全屏独立应用，手写草稿与错题进度自动保存在你自己的设备本地，已打开过的试卷支持离线刷题。

## 核心特性

1. **纯净无文理综 2018–2026 高考题库**
   - 收录 **192 套可交互结构化试卷、3,522 道独立小题**（覆盖数学、物理、语文，含自动核对答案、配图与 KaTeX 公式渲染，全库 **80,910 条公式**已通过自动化 KaTeX 解析校验）。
   - 严格过滤掉旧高考文综/理综及传统文理科卷，专注于新高考命题体系。
2. **平板级屏幕画笔演算与本地离线存储**
   - 模仿 Apple Notes / GoodNotes 手感：双栏演算、题面直接圈画、纯净做题三种模式无缝切换。
   - **100% 纯静态前端架构**：支持 Apple Pencil / 手写笔 / 鼠标平滑贝塞尔曲线压感演算，所有草稿笔记、计时进度与错题本均通过浏览器 `IndexedDB` 保存在本地，无需注册登录、无需后台服务器与数据库。
   - 支持 **PWA（添加到 iPad/手机主屏幕）**：打开网站即可一键添加到 iPadOS / 安卓桌面全屏运行，已加载试卷支持离线刷题。
3. **面向不同水平的「分层多解灵魂」**
   - [enrichment/](gaokao-papers/enrichment) 层将官方通法与多梯度的解题思维结合：
     - 💡 **破题直觉**：零门槛看清题眼、第一眼从哪里下手
     - 📘 **规范通法**：保留标准满分步骤，稳拿解答步骤分
     - ⚡ **考场快解**：特值法、极化恒等式、俯视图降维、切线放缩、量纲与极限角检验等提速技巧
     - 🚀 **高阶视野**：揭示母题结构与数学/物理思想之美
     - ✨ **一句点睛 + ⚠️ 考场避坑提醒**
   - 已上线 **12 套旗舰整卷共 218 题全题精讲**：`2026 · 新课标全国Ⅰ卷 · 数学`（19 题）、`2026 · 新课标全国Ⅱ卷 · 数学`（19 题）、`2025 · 新课标全国Ⅰ卷 · 数学`（19 题）、`2025 · 新课标全国Ⅱ卷 · 数学`（19 题）、`2024 · 新高考全国Ⅰ卷 · 数学`（19 题）、`2024 · 新高考全国Ⅱ卷 · 数学`（19 题）、`2023 · 新高考全国Ⅰ卷 · 数学`（22 题）、`2023 · 新高考全国Ⅱ卷 · 数学`（22 题）、`2026 · 广东卷 · 物理`（15 题）、`2026 · 湖南卷 · 物理`（15 题）、`2026 · 湖北卷 · 物理`（15 题）、`2025 · 广东卷 · 物理`（15 题），持续迭代补全中。

---

## 目录结构

```text
.
├── gaokao-app/                  # React + Vite 前端与平板草稿本工作台（含 PWA 支持）
│   ├── public/                  # 应用图标、manifest.webmanifest、离线 Service Worker
│   └── src/                     # 核心组件（LibraryView、PracticeWorkspace、ScratchpadCanvas、MathContent）
└── gaokao-papers/
    ├── bank/                    # 结构化题库 JSON + 题图/解图（约 94 MB，可直接随静态前端发布）
    ├── enrichment/              # 原创分层多解与避坑叠加层（随构建脚本合并进题库，更新不丢失）
    ├── inventory/               # 全库盘点与质量审计报告
    └── scripts/                 # LaTeX 规范化清洗、题库重构与校验脚本
```

> 注：`gaokao-papers/collected/`（约 11.7 GB 全九科图文原卷与 PDF）及 `gaokao-papers/sources/`（上游原始仓库克隆）体积较大，已通过 `.gitignore` 排除在 Git 仓库之外；在线精简静态版默认只内置 94 MB 的 192 套结构化交互题库，需要挂载全套图文包时可通过环境变量 `VITE_COLLECTED_BASE` 指向外置对象存储或本地目录。

---

## 开发者本地运行与二次开发（普通学生无需看此步）

> 说明：以下 `http://127.0.0.1:5173/` 是**开发者把自己电脑当作本地测试服务器**时的本机地址。如果只是做题复习，请直接打开上方线上网址 https://mojuan-gaokao.pages.dev ，不要运行下面命令。

### 1. 在自己电脑上启动开发调试服务

需要 Node.js 18+：

```bash
cd gaokao-app
npm install
npm run dev
```

打开浏览器访问**你自己电脑上的本机预览地址** `http://127.0.0.1:5173/` 即可调试体验。

### 2. 一键构建可部署的纯静态包

```bash
cd gaokao-app
npm run build
```

构建脚本会自动将 `gaokao-papers/bank/` 打包进 `gaokao-app/dist/bank/`，生成的 `gaokao-app/dist/` 就是一个**完全自包含的静态网站文件夹**（可直接部署到 Cloudflare Pages、Vercel、GitHub Pages 或任意 Nginx 静态空间）。

如果部署在 GitHub Pages 子路径（如 `/mojuan-gaokao/`），构建时指定 `VITE_APP_BASE` 即可：

```bash
VITE_APP_BASE=/mojuan-gaokao/ npm run build
```

### 3. 重新合并分层多解与校验题库（Python 3.10+）

修改或新增 `gaokao-papers/enrichment/<paper_id>.json` 后运行：

```bash
python gaokao-papers/scripts/build_structured_bank.py
python gaokao-papers/scripts/validate_bank.py
```

---

## 免费上线部署（Cloudflare Pages 示例）

1. 将本仓库推送至 GitHub；
2. 在 Cloudflare Pages 中连接该 GitHub 仓库：
   - **Build command**: `cd gaokao-app && npm ci && npm run build`
   - **Build output directory**: `gaokao-app/dist`
3. 之后每次向 GitHub 推送代码或新的 `enrichment/` 多解，网站都会自动重新构建上线。

---

## 开源致谢与许可

- 本项目前端代码与处理脚本采用 **MIT License** 开源，原创分层多解内容采用 **CC BY-NC-SA 4.0（公益非商业性使用）**；详细条款见 [LICENSE](LICENSE)。
- 题库原始 LaTeX 与试卷整理致谢开源社区贡献者，包括 [YLXDXX/gaokao-physics-archive](https://github.com/YLXDXX/gaokao-physics-archive)、[DxAThing/Gaokao-Math-Problems-Compilation](https://github.com/DxAThing/Gaokao-Math-Problems-Compilation)、[deekur/gaokaomath](https://github.com/deekur/gaokaomath) 等项目。
