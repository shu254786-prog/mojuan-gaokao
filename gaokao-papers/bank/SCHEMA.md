# Gaokao Interactive Question Bank Schema (`bank/`)

## 1. 目录结构

```text
bank/
├── index.json               # 全库统一索引（结构化单题卷 + 图文卷 + 原卷PDF）
├── README.md                # 结构化题库覆盖与题型统计
├── SCHEMA.md                # 本规范说明
├── papers/                  # 结构化单卷 JSON（数学、物理、语文）
│   ├── 2025-math-national_paper_1.json
│   ├── 2025-physics-广东.json
│   └── 2026-chinese-全国I卷_gzywtk_3057.json
└── assets/                  # 按年份/科目/考区归档的 PNG/SVG 题图与解图
    └── 2025/physics/广东/02.png
```

## 2. `papers/<id>.json` 数据结构

```json
{
  "id": "2025-physics-广东",
  "year": 2025,
  "subject": "物理",
  "region": "广东卷",
  "region_key": "广东",
  "format_tier": "structured_latex",
  "question_count": 15,
  "source": "gaokao-physics-archive",
  "questions": [
    {
      "qid": "2025-physics-广东-q02",
      "number": 2,
      "section": "单选题",
      "type": "single_choice | multiple_choice | fill_blank | open_ended",
      "score": 4,
      "difficulty": 650,
      "topics": ["电磁感应", "远距离输电"],
      "stem_md": "KaTeX ($...$ / $$...$$) + Markdown + ![配图](assets/...)",
      "figures": ["assets/2025/physics/广东/02.png"],
      "choices": [
        { "key": "A", "text_md": "...", "image": null }
      ],
      "answer": {
        "raw": "B",
        "choices": ["B"],
        "sub_answers": ["0.58", "最小"]
      },
      "solution_methods": [
        {
          "id": "method_1",
          "label": "标准解析",
          "tier": "standard | alternative",
          "content_md": "..."
        }
      ],
      "solution_figures": [],
      "has_multi_method": false
    }
  ]
}
```
