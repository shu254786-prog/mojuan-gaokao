import React, { useMemo, useState } from "react";
import { BookOpen, CheckCircle2, FileText, Image, Search, Sparkles, AlertCircle } from "lucide-react";

const SUBJECTS = ["全部", "数学", "物理", "语文", "英语", "化学", "生物", "政治", "历史", "地理", "全科九科汇总"];
const YEARS = ["全部", 2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018];

const SUBJ_STYLE = {
  数学: { bg: "rgba(0, 113, 227, 0.11)", fg: "#0071E3" },
  物理: { bg: "rgba(88, 86, 214, 0.12)", fg: "#5856D6" },
  语文: { bg: "rgba(255, 149, 0, 0.13)", fg: "#C96A00" },
  英语: { bg: "rgba(52, 199, 89, 0.13)", fg: "#1D8A3C" },
  化学: { bg: "rgba(175, 82, 222, 0.12)", fg: "#8944AB" },
  生物: { bg: "rgba(48, 176, 199, 0.13)", fg: "#0E7A8D" },
  政治: { bg: "rgba(255, 59, 48, 0.11)", fg: "#D92B22" },
  历史: { bg: "rgba(162, 132, 94, 0.15)", fg: "#7D5E38" },
  地理: { bg: "rgba(50, 173, 230, 0.13)", fg: "#0B78A8" },
  全科九科汇总: { bg: "rgba(142, 142, 147, 0.15)", fg: "#636366" },
};

export default function LibraryView({ indexData, progressMap, onSelectPaper }) {
  const [tierMode, setTierMode] = useState("structured"); // structured | all | wrong
  const [subject, setSubject] = useState("全部");
  const [year, setYear] = useState("全部");
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(60);

  const items = indexData?.items || [];

  const wrongPaperIds = useMemo(() => {
    const s = new Set();
    for (const [pid, prog] of Object.entries(progressMap)) {
      if (prog.wrongQids && prog.wrongQids.length > 0) s.add(pid);
    }
    return s;
  }, [progressMap]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return items.filter((item) => {
      if (tierMode === "structured") {
        if (item.format_tier !== "structured_latex" && item.format_tier !== "structured_text") return false;
      } else if (tierMode === "enriched") {
        if (!(item.enriched_count > 0 || item.multi_method_count > 0)) return false;
      } else if (tierMode === "wrong") {
        if (!wrongPaperIds.has(item.id)) return false;
      }
      if (subject !== "全部" && item.subject !== subject) return false;
      if (year !== "全部" && item.year !== year) return false;
      if (q) {
        const hay = `${item.year} ${item.subject} ${item.region} ${item.title || ""}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [items, tierMode, subject, year, query, wrongPaperIds]);

  const visible = filtered.slice(0, limit);
  const stats = indexData?.stats || {};
  const structuredTotalQ = (stats.math_q || 0) + (stats.phys_q || 0) + (stats.chi_q || 0);
  const structuredTotalP = (stats.math_papers || 0) + (stats.phys_papers || 0) + (stats.chi_papers || 0);
  const multiPaperCount = useMemo(
    () => items.filter((it) => it.enriched_count > 0 || it.multi_method_count > 0).length,
    [items]
  );

  return (
    <div className="library-shell">
      <div className="hero-banner">
        <div>
          <h1 className="hero-title">高考真题与屏幕演算实验室</h1>
          <p className="hero-subtitle">
            专注 2018–2026 全国无文理综新高考真题 · 纯净免费 · 支持平板级手写笔草稿与多解法对照
          </p>
        </div>

        <div className="stats-strip">
          <div className="stat-chip">
            <div className="num">{structuredTotalQ.toLocaleString()}</div>
            <div className="lbl">可交互判分单题（{structuredTotalP} 套）</div>
          </div>
          <div className="stat-chip">
            <div className="num">{(stats.web_packs || 0).toLocaleString()}</div>
            <div className="lbl">全 9 科真题图文包</div>
          </div>
          <div className="stat-chip">
            <div className="num">{wrongPaperIds.size}</div>
            <div className="lbl">含错题待复习试卷</div>
          </div>
        </div>
      </div>

      <div className="filter-card">
        <div className="filter-row" style={{ justifyContent: "space-between" }}>
          <div className="segmented">
            <button
              className={tierMode === "structured" ? "active" : ""}
              onClick={() => { setTierMode("structured"); setLimit(60); }}
            >
              <Sparkles size={13} style={{ marginRight: 5, verticalAlign: -2 }} />
              可交互做题 · 单题结构化 ({structuredTotalP})
            </button>
            <button
              className={tierMode === "enriched" ? "active" : ""}
              onClick={() => { setTierMode("enriched"); setLimit(60); }}
            >
              分层多解 · 精讲卷 ({multiPaperCount})
            </button>
            <button
              className={tierMode === "all" ? "active" : ""}
              onClick={() => { setTierMode("all"); setLimit(60); }}
            >
              全部真题库 · 含全9科图文与PDF ({items.length})
            </button>
            <button
              className={tierMode === "wrong" ? "active" : ""}
              onClick={() => { setTierMode("wrong"); setLimit(60); }}
            >
              <AlertCircle size={13} style={{ marginRight: 5, verticalAlign: -2 }} />
              我的错题本 ({wrongPaperIds.size})
            </button>
          </div>

          <div className="search-box">
            <Search size={15} color="var(--text-3)" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="搜索省份、卷别或年份（如：广东、全国Ⅰ卷、2025）"
            />
          </div>
        </div>

        <div className="filter-row">
          <span className="filter-label">科目</span>
          {SUBJECTS.filter((s) =>
            tierMode === "structured" || tierMode === "enriched" ? ["全部", "数学", "物理", "语文"].includes(s) : true
          ).map((s) => (
            <button
              key={s}
              className={`pill-btn ${subject === s ? "active" : ""}`}
              onClick={() => setSubject(s)}
            >
              {s}
            </button>
          ))}
        </div>

        <div className="filter-row">
          <span className="filter-label">年份</span>
          {YEARS.map((y) => (
            <button
              key={y}
              className={`pill-btn ${year === y ? "active" : ""}`}
              onClick={() => setYear(y)}
            >
              {y === "全部" ? "全部年份" : `${y}年`}
            </button>
          ))}
        </div>
      </div>

      {visible.length === 0 ? (
        <div
          style={{
            textAlign: "center",
            padding: "64px 20px",
            color: "var(--text-2)",
            background: "var(--bg-card)",
            borderRadius: 18,
            border: "1px solid var(--border)",
          }}
        >
          没有匹配到符合条件的试卷，换个年份或搜索词试试。
        </div>
      ) : (
        <>
          <div className="paper-grid">
            {visible.map((item) => {
              const st = SUBJ_STYLE[item.subject] || SUBJ_STYLE["全科九科汇总"];
              const isInteractive =
                item.format_tier === "structured_latex" || item.format_tier === "structured_text";
              const prog = progressMap[item.id];
              const doneCount = prog ? Object.keys(prog.results || {}).length : 0;
              const wrongCount = prog?.wrongQids?.length || 0;

              return (
                <div key={item.id} className="paper-card" onClick={() => onSelectPaper(item)}>
                  <div>
                    <div className="paper-card-top">
                      <span className="subj-badge" style={{ background: st.bg, color: st.fg }}>
                        {item.year} · {item.subject}
                      </span>
                      <span
                        className={`tier-badge ${
                          item.enriched_count > 0
                            ? "enriched"
                            : isInteractive
                              ? "interactive"
                              : ""
                        }`}
                      >
                        {item.enriched_count > 0
                          ? `分层多解 ${item.enriched_count} 题`
                          : item.multi_method_count > 0
                            ? `含多解 ${item.multi_method_count} 题`
                            : isInteractive
                              ? "在线交互做题"
                              : item.format_tier === "pdf_original"
                                ? "原卷 PDF"
                                : "图文原卷"}
                      </span>
                    </div>
                    <div className="paper-card-title" style={{ marginTop: 10 }}>
                      {item.region || item.title}
                    </div>
                    {item.title && item.region && item.title !== item.region && (
                      <div
                        style={{
                          fontSize: 12.5,
                          color: "var(--text-2)",
                          marginTop: 4,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {item.title}
                      </div>
                    )}
                  </div>

                  <div className="paper-card-meta">
                    <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
                      {isInteractive ? (
                        <>
                          <BookOpen size={13} /> {item.question_count} 道单题
                        </>
                      ) : item.format_tier === "pdf_original" ? (
                        <>
                          <FileText size={13} /> PDF 整卷演算
                        </>
                      ) : (
                        <>
                          <Image size={13} /> {item.image_count || 0} 张页图
                        </>
                      )}
                    </span>

                    {doneCount > 0 && (
                      <span style={{ display: "inline-flex", alignItems: "center", gap: 6, color: wrongCount ? "var(--orange)" : "var(--green)", fontWeight: 600 }}>
                        <CheckCircle2 size={13} />
                        已练 {doneCount}
                        {wrongCount > 0 ? ` · 错 ${wrongCount}` : ""}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {filtered.length > visible.length && (
            <div style={{ textAlign: "center", marginTop: 28 }}>
              <button className="icon-btn primary" style={{ height: 38, padding: "0 22px" }} onClick={() => setLimit((l) => l + 60)}>
                继续加载更多（当前显示 {visible.length} / {filtered.length}）
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
