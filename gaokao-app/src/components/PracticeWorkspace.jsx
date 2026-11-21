import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  Bookmark,
  BookOpen,
  Check,
  ChevronLeft,
  ChevronRight,
  Clock,
  Compass,
  Eye,
  EyeOff,
  FileText,
  Layers,
  Lightbulb,
  Moon,
  PenLine,
  Rocket,
  Sparkles,
  Sun,
  X,
  Zap,
} from "lucide-react";
import MathContent from "./MathContent";
import ScratchpadCanvas from "./ScratchpadCanvas";
import { loadAllStrokeKeys, loadPaperProgress, savePaperProgress } from "../utils/storage";
import { bankUrl, collectedUrl } from "../utils/paths";

const TIER_UI = {
  intuition: { Icon: Lightbulb, tag: "破题直觉" },
  standard: { Icon: BookOpen, tag: "规范通法" },
  fast: { Icon: Zap, tag: "考场快解" },
  alternative: { Icon: Compass, tag: "另辟蹊径" },
  advanced: { Icon: Rocket, tag: "高阶视野" },
};

function formatTimer(sec) {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export default function PracticeWorkspace({
  paperMeta,
  dark,
  onToggleDark,
  onBack,
  onProgressUpdated,
}) {
  const [paperData, setPaperData] = useState(null);
  const [packMeta, setPackMeta] = useState(null);
  const [packText, setPackText] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [qIdx, setQIdx] = useState(0);
  const [layoutMode, setLayoutMode] = useState("split"); // split | overlay | clean
  const [splitPct, setSplitPct] = useState(50);
  const [overlayPenActive, setOverlayPenActive] = useState(true);
  const [showSolution, setShowSolution] = useState(false);
  const [methodIdx, setMethodIdx] = useState(0);
  const [showPackText, setShowPackText] = useState(false);

  const [progress, setProgress] = useState({
    paperId: paperMeta.id,
    answers: {},
    results: {},
    wrongQids: [],
  });
  const [strokeKeys, setStrokeKeys] = useState(new Set());
  const [seconds, setSeconds] = useState(0);
  const [timerPaused, setTimerPaused] = useState(false);

  const draggingSplitRef = useRef(false);

  // Load paper data
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    setPaperData(null);
    setPackMeta(null);
    setPackText("");
    setQIdx(0);
    setShowSolution(false);

    async function load() {
      try {
        if (paperMeta.format_tier === "structured_latex" || paperMeta.format_tier === "structured_text") {
          const resp = await fetch(bankUrl(paperMeta.paper_file));
          if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
          const data = await resp.json();
          if (!cancelled) setPaperData(data);
        } else if (paperMeta.format_tier === "page_images") {
          const dirUrl = collectedUrl(paperMeta.collected_dir);
          const resp = await fetch(`${dirUrl}/meta.json`);
          if (resp.status === 404) {
            throw new Error("当前在线静态版仅内置 192 套结构化交互题库（3,522 题）；11.7 GB 全九科图文原卷包需挂载本地 collected 目录或外部对象存储后访问。");
          }
          if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
          const m = await resp.json();
          if (!cancelled) setPackMeta({ ...m, baseUrl: dirUrl });
          if (m.text_length > 0) {
            fetch(`${dirUrl}/content.txt`)
              .then((r) => (r.ok ? r.text() : ""))
              .then((t) => {
                if (!cancelled) setPackText(t);
              })
              .catch(() => {});
          }
        }
      } catch (err) {
        if (!cancelled) setError(err.message || "加载试卷失败");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();

    loadPaperProgress(paperMeta.id).then((p) => {
      if (!cancelled) setProgress(p);
    });
    loadAllStrokeKeys().then((keys) => {
      if (!cancelled) setStrokeKeys(keys);
    });

    return () => {
      cancelled = true;
    };
  }, [paperMeta]);

  // Timer
  useEffect(() => {
    if (timerPaused) return;
    const t = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, [timerPaused]);

  // Resizable split drag
  useEffect(() => {
    const onMove = (e) => {
      if (!draggingSplitRef.current) return;
      const pct = (e.clientX / window.innerWidth) * 100;
      setSplitPct(Math.max(30, Math.min(72, pct)));
    };
    const onUp = () => {
      draggingSplitRef.current = false;
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
  }, []);

  const questions = paperData?.questions || [];
  const currentQ = questions[qIdx] || null;
  const activeQid = currentQ ? currentQ.qid : paperMeta.id;

  const updateProgress = useCallback(
    (updater) => {
      setProgress((prev) => {
        const next = updater(prev);
        savePaperProgress(next);
        onProgressUpdated?.(next);
        return next;
      });
    },
    [onProgressUpdated]
  );

  // Reset solution tab when changing question
  useEffect(() => {
    setMethodIdx(0);
    if (currentQ) {
      const hasResult = Boolean(progress.results?.[currentQ.qid]);
      setShowSolution(hasResult);
    }
  }, [qIdx, currentQ?.qid]);

  const handleSelectChoice = (key) => {
    if (!currentQ) return;
    const isMulti = currentQ.type === "multiple_choice";
    updateProgress((prev) => {
      const cur = prev.answers[currentQ.qid] || [];
      let nextAns;
      if (isMulti) {
        nextAns = cur.includes(key) ? cur.filter((k) => k !== key) : [...cur, key].sort();
      } else {
        nextAns = [key];
      }
      return {
        ...prev,
        answers: { ...prev.answers, [currentQ.qid]: nextAns },
      };
    });
  };

  const handleBlankInput = (idx, val) => {
    if (!currentQ) return;
    updateProgress((prev) => {
      const cur = Array.isArray(prev.answers[currentQ.qid]) ? [...prev.answers[currentQ.qid]] : [];
      cur[idx] = val;
      return { ...prev, answers: { ...prev.answers, [currentQ.qid]: cur } };
    });
  };

  const handleCheckAnswer = () => {
    if (!currentQ) return;
    let verdict = "reviewed";
    if (currentQ.type === "single_choice" || currentQ.type === "multiple_choice") {
      const expected = [...(currentQ.answer?.choices || [])].sort().join("");
      const actual = [...(progress.answers[currentQ.qid] || [])].sort().join("");
      if (expected) {
        verdict = expected === actual ? "correct" : "wrong";
      }
    }
    updateProgress((prev) => {
      const wrongSet = new Set(prev.wrongQids || []);
      if (verdict === "wrong") wrongSet.add(currentQ.qid);
      else if (verdict === "correct") wrongSet.delete(currentQ.qid);
      return {
        ...prev,
        results: { ...prev.results, [currentQ.qid]: verdict },
        wrongQids: Array.from(wrongSet),
      };
    });
    setShowSolution(true);
  };

  const handleSelfAssess = (verdict) => {
    if (!currentQ) return;
    updateProgress((prev) => {
      const wrongSet = new Set(prev.wrongQids || []);
      if (verdict === "wrong") wrongSet.add(currentQ.qid);
      else wrongSet.delete(currentQ.qid);
      return {
        ...prev,
        results: { ...prev.results, [currentQ.qid]: verdict },
        wrongQids: Array.from(wrongSet),
      };
    });
  };

  const toggleWrongBookmark = () => {
    if (!currentQ) return;
    updateProgress((prev) => {
      const wrongSet = new Set(prev.wrongQids || []);
      if (wrongSet.has(currentQ.qid)) wrongSet.delete(currentQ.qid);
      else wrongSet.add(currentQ.qid);
      return { ...prev, wrongQids: Array.from(wrongSet) };
    });
  };

  const handleStrokePresence = useCallback(
    (layer) => (has) => {
      const k = `${activeQid}:${layer}`;
      setStrokeKeys((prev) => {
        const hasNow = prev.has(k);
        if (hasNow === has) return prev;
        const next = new Set(prev);
        if (has) next.add(k);
        else next.delete(k);
        return next;
      });
    },
    [activeQid]
  );

  const isWrongMarked = currentQ ? (progress.wrongQids || []).includes(currentQ.qid) : false;
  const currentResult = currentQ ? progress.results?.[currentQ.qid] : null;
  const userChoiceArr = currentQ ? progress.answers?.[currentQ.qid] || [] : [];

  const isPictureChoices = useMemo(() => {
    if (!currentQ?.choices?.length) return false;
    return currentQ.choices.some((c) => Boolean(c.image));
  }, [currentQ]);

  const solutionMethods = currentQ?.solution_methods || [];
  const activeMethod = solutionMethods[methodIdx] || solutionMethods[0] || null;

  return (
    <div className="workspace-root">
      {/* Unified Apple Frosted Navbar */}
      <header className="apple-navbar">
        <div style={{ display: "flex", alignItems: "center", gap: 10, minWidth: 0 }}>
          <button className="icon-btn" onClick={onBack}>
            <ArrowLeft size={15} /> 大厅
          </button>
          <div style={{ fontWeight: 600, fontSize: 14.5, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {paperMeta.year} · {paperMeta.region || paperMeta.title} · {paperMeta.subject}
          </div>
        </div>

        {/* Question Pills */}
        {questions.length > 0 && (
          <div className="q-strip">
            {questions.map((q, idx) => {
              const res = progress.results?.[q.qid];
              const hasPen = strokeKeys.has(`${q.qid}:scratch`) || strokeKeys.has(`${q.qid}:overlay`);
              return (
                <button
                  key={q.qid}
                  className={`q-dot ${idx === qIdx ? "current" : ""} ${res === "correct" ? "correct" : res === "wrong" ? "wrong" : ""}`}
                  onClick={() => setQIdx(idx)}
                  title={`第 ${q.number} 题`}
                >
                  {q.number}
                  {hasPen && <span className="pen-pip" />}
                </button>
              );
            })}
          </div>
        )}

        {/* Controls */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
          <div className="segmented">
            <button className={layoutMode === "split" ? "active" : ""} onClick={() => setLayoutMode("split")}>
              双栏演算
            </button>
            <button className={layoutMode === "overlay" ? "active" : ""} onClick={() => setLayoutMode("overlay")}>
              题面圈画
            </button>
            <button className={layoutMode === "clean" ? "active" : ""} onClick={() => setLayoutMode("clean")}>
              纯净做题
            </button>
          </div>

          <button
            className="icon-btn"
            onClick={() => setTimerPaused((p) => !p)}
            title="点击暂停/继续计时"
            style={{ fontVariantNumeric: "tabular-nums" }}
          >
            <Clock size={14} /> {formatTimer(seconds)}
          </button>

          <button className="icon-btn" onClick={onToggleDark} title="切换浅色 / 深色模式">
            {dark ? <Sun size={15} /> : <Moon size={15} />}
          </button>
        </div>
      </header>

      {/* Main Split Body */}
      <div className="workspace-split">
        {/* LEFT PANE: Question / Exam Viewer */}
        <section
          className="question-pane"
          style={{
            width: layoutMode === "split" ? `${splitPct}%` : "100%",
            flexShrink: 0,
          }}
        >
          {/* Transparent Overlay Pen Layer (active when layoutMode === "overlay") */}
          {layoutMode === "overlay" && (
            <div className={`overlay-canvas-wrap ${overlayPenActive ? "drawing-active" : ""}`}>
              <ScratchpadCanvas
                storageKey={`${activeQid}:overlay`}
                dark={dark}
                transparent
                interactive={overlayPenActive}
                showDock={overlayPenActive}
                onHasStrokesChange={handleStrokePresence("overlay")}
              />
            </div>
          )}

          {layoutMode === "overlay" && (
            <div style={{ position: "fixed", top: 68, right: 24, zIndex: 35 }}>
              <button
                className={`icon-btn ${overlayPenActive ? "primary" : ""}`}
                onClick={() => setOverlayPenActive((v) => !v)}
              >
                <PenLine size={14} /> {overlayPenActive ? "圈画模式中（点击切回选答案）" : "开启题面圈画"}
              </button>
            </div>
          )}

          {loading ? (
            <div style={{ textAlign: "center", padding: 60, color: "var(--text-2)" }}>正在加载真题内容...</div>
          ) : error ? (
            <div style={{ textAlign: "center", padding: 60, color: "var(--red)" }}>加载失败：{error}</div>
          ) : paperMeta.format_tier === "pdf_original" ? (
            <div style={{ height: "calc(100vh - 110px)" }}>
              <iframe
                src={collectedUrl(paperMeta.pdf_path)}
                title={paperMeta.region}
                style={{ width: "100%", height: "100%", border: "none", borderRadius: 16, background: "#fff" }}
              />
            </div>
          ) : packMeta ? (
            <div className="question-inner">
              <div className="q-card" style={{ marginBottom: 16 }}>
                <div className="q-header" style={{ marginBottom: 10 }}>
                  <div className="q-tags">
                    <span className="tag-chip">{packMeta.year} 年</span>
                    <span className="tag-chip">{packMeta.subject}</span>
                    <span className="tag-chip">{packMeta.region}</span>
                    <span className="tag-chip">共 {packMeta.saved_images?.length || 0} 页试卷图</span>
                  </div>
                  {packText && (
                    <button className="icon-btn" onClick={() => setShowPackText((v) => !v)}>
                      <FileText size={14} /> {showPackText ? "隐藏提取文本" : "查看提取文本"}
                    </button>
                  )}
                </div>
                <div style={{ fontSize: 15, fontWeight: 600 }}>{packMeta.title}</div>
                {showPackText && packText && (
                  <pre
                    style={{
                      marginTop: 14,
                      whiteSpace: "pre-wrap",
                      fontFamily: "inherit",
                      fontSize: 14,
                      lineHeight: 1.75,
                      background: "var(--bg-app)",
                      padding: 16,
                      borderRadius: 12,
                      maxHeight: 420,
                      overflowY: "auto",
                    }}
                  >
                    {packText}
                  </pre>
                )}
              </div>

              {(packMeta.saved_images || []).map((imgName, i) => (
                <img
                  key={imgName}
                  className="exam-page-img"
                  src={`${packMeta.baseUrl}/${imgName}`}
                  alt={`第 ${i + 1} 页`}
                  loading="lazy"
                />
              ))}
            </div>
          ) : currentQ ? (
            <div className="question-inner">
              <div className="q-card">
                <div className="q-header">
                  <div className="q-tags">
                    <span style={{ fontWeight: 700, fontSize: 16 }}>第 {currentQ.number} 题</span>
                    <span className="tag-chip">{currentQ.section}</span>
                    {currentQ.score != null && <span className="tag-chip">{currentQ.score} 分</span>}
                    {currentQ.difficulty != null && (
                      <span className="tag-chip" title="数值越小难度越高">
                        难度指数 {currentQ.difficulty}
                      </span>
                    )}
                    {currentQ.is_enriched ? (
                      <span className="tier-badge enriched">分层多解 · {(currentQ.solution_methods || []).length} 种视角</span>
                    ) : currentQ.has_multi_method ? (
                      <span className="tier-badge interactive">多解法 · {(currentQ.solution_methods || []).length} 种</span>
                    ) : null}
                    {Array.from(new Set(currentQ.topics || [])).map((t) => (
                      <span key={t} className="tag-chip" style={{ background: "var(--accent-soft)", color: "var(--accent)" }}>
                        {t}
                      </span>
                    ))}
                  </div>

                  <button
                    className={`icon-btn ${isWrongMarked ? "active" : ""}`}
                    onClick={toggleWrongBookmark}
                    title="加入/移出本地错题本"
                  >
                    <Bookmark size={14} fill={isWrongMarked ? "currentColor" : "none"} />
                    {isWrongMarked ? "已收进错题本" : "收藏错题"}
                  </button>
                </div>

                {/* Stem */}
                <MathContent content={currentQ.stem_md} />

                {/* Choices */}
                {currentQ.choices && currentQ.choices.length > 0 && (
                  <div className={`choices-list ${isPictureChoices ? "picture-grid" : ""}`}>
                    {currentQ.choices.map((ch) => {
                      const selected = userChoiceArr.includes(ch.key);
                      const expectedArr = currentQ.answer?.choices || [];
                      let statusCls = "";
                      if (currentResult && showSolution && expectedArr.length > 0) {
                        if (expectedArr.includes(ch.key)) statusCls = "correct";
                        else if (selected) statusCls = "wrong";
                      } else if (selected) {
                        statusCls = "selected";
                      }

                      return (
                        <button
                          key={ch.key}
                          className={`choice-btn ${statusCls}`}
                          onClick={() => handleSelectChoice(ch.key)}
                        >
                          <span className="choice-key">{ch.key}</span>
                          <div className="choice-body">
                            {ch.image && (
                              <img src={bankUrl(ch.image)} alt={`选项 ${ch.key}`} />
                            )}
                            {ch.text_md && <MathContent content={ch.text_md} />}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                )}

                {/* Fill-in Blanks */}
                {currentQ.type === "fill_blank" && (
                  <div className="blank-inputs">
                    {(currentQ.answer?.sub_answers?.length ? currentQ.answer.sub_answers : [""]).map((_, idx) => (
                      <div key={idx} className="blank-row">
                        <span style={{ fontSize: 13, color: "var(--text-2)", width: 52 }}>
                          第 {idx + 1} 空
                        </span>
                        <input
                          value={(Array.isArray(userChoiceArr) ? userChoiceArr[idx] : "") || ""}
                          onChange={(e) => handleBlankInput(idx, e.target.value)}
                          placeholder="在右侧草稿纸演算后可在此输入答案核对..."
                        />
                      </div>
                    ))}
                  </div>
                )}

                {/* Action Bar */}
                <div
                  style={{
                    marginTop: 22,
                    paddingTop: 16,
                    borderTop: "1px solid var(--border)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    flexWrap: "wrap",
                    gap: 10,
                  }}
                >
                  <div style={{ display: "flex", gap: 8 }}>
                    <button
                      className="icon-btn"
                      disabled={qIdx === 0}
                      onClick={() => setQIdx((i) => Math.max(0, i - 1))}
                    >
                      <ChevronLeft size={15} /> 上一题
                    </button>
                    <button
                      className="icon-btn"
                      disabled={qIdx >= questions.length - 1}
                      onClick={() => setQIdx((i) => Math.min(questions.length - 1, i + 1))}
                    >
                      下一题 <ChevronRight size={15} />
                    </button>
                  </div>

                  <div style={{ display: "flex", gap: 8 }}>
                    {(currentQ.type === "single_choice" ||
                      currentQ.type === "multiple_choice" ||
                      currentQ.type === "fill_blank") && (
                      <button className="icon-btn primary" onClick={handleCheckAnswer}>
                        <Check size={15} /> 提交并核对答案
                      </button>
                    )}
                    <button className="icon-btn" onClick={() => setShowSolution((s) => !s)}>
                      {showSolution ? <EyeOff size={14} /> : <Eye size={14} />}
                      {showSolution ? "收起解析" : "查看思路与多解"}
                    </button>
                  </div>
                </div>
              </div>

              {/* Solutions & Multi-Method Panel */}
              {showSolution && (
                <div className="solution-card">
                  <div className="solution-header">
                    <div className="answer-banner">
                      <Check size={15} />
                      参考答案：{currentQ.answer?.raw ? <MathContent content={currentQ.answer.raw} /> : "见下方详解"}
                    </div>

                    <div style={{ display: "flex", gap: 8 }}>
                      <button
                        className={`icon-btn ${currentResult === "correct" ? "active" : ""}`}
                        onClick={() => handleSelfAssess("correct")}
                      >
                        <Check size={14} /> 做对了
                      </button>
                      <button
                        className={`icon-btn ${currentResult === "wrong" ? "active" : ""}`}
                        onClick={() => handleSelfAssess("wrong")}
                      >
                        <X size={14} /> 卡住了 · 记错题
                      </button>
                    </div>
                  </div>

                  {solutionMethods.length > 0 ? (
                    <>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                        <span style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 13, fontWeight: 600, color: "var(--text-2)" }}>
                          <Layers size={14} /> 解法视角（按水平与提速梯度切换）：
                        </span>
                      </div>

                      <div className="method-tabs">
                        {solutionMethods.map((m, idx) => {
                          const tier = m.tier || "standard";
                          const meta = TIER_UI[tier] || TIER_UI.standard;
                          const TierIcon = meta.Icon;
                          return (
                            <button
                              key={m.id}
                              className={`method-tab tier-${tier} ${idx === methodIdx ? "active" : ""}`}
                              onClick={() => setMethodIdx(idx)}
                            >
                              <TierIcon size={14} />
                              <MathContent inline content={m.label} />
                            </button>
                          );
                        })}
                      </div>

                      {activeMethod && (activeMethod.audience || activeMethod.time_save || activeMethod.badge) && (
                        <div className="method-meta-bar">
                          {activeMethod.badge && (
                            <span className="method-pill">
                              <MathContent inline content={activeMethod.badge} />
                            </span>
                          )}
                          {activeMethod.audience && (
                            <span>
                              适合：<MathContent inline content={activeMethod.audience} />
                            </span>
                          )}
                          {activeMethod.time_save && (
                            <span style={{ marginLeft: "auto", fontWeight: 600, color: "var(--accent)" }}>
                              {activeMethod.time_save}
                            </span>
                          )}
                        </div>
                      )}

                      {activeMethod && <MathContent content={activeMethod.content_md} />}
                    </>
                  ) : (
                    <div style={{ color: "var(--text-2)", fontSize: 14 }}>
                      该题暂无文字详解，可先核对上方参考答案。
                    </div>
                  )}

                  {(currentQ.takeaway || currentQ.pitfall) && (
                    <div className="insight-grid">
                      {currentQ.takeaway && (
                        <div className="insight-box takeaway">
                          <div className="insight-title">
                            <Sparkles size={14} /> 解题魅力 · 一句点睛与母题迁移
                          </div>
                          <MathContent content={currentQ.takeaway} />
                        </div>
                      )}
                      {currentQ.pitfall && (
                        <div className="insight-box pitfall">
                          <div className="insight-title">
                            <AlertTriangle size={14} /> 考场避坑提醒
                          </div>
                          <MathContent content={currentQ.pitfall} />
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : null}
        </section>

        {/* RESIZABLE DIVIDER */}
        {layoutMode === "split" && (
          <div
            className="split-resizer"
            onPointerDown={() => {
              draggingSplitRef.current = true;
            }}
            title="拖动调整题目与草稿本比例"
          >
            <div className="split-grabber" />
          </div>
        )}

        {/* RIGHT PANE: iPadOS Tablet Scratchpad */}
        {layoutMode === "split" && (
          <section className="scratchpad-pane" style={{ flex: 1 }}>
            <div
              style={{
                position: "absolute",
                top: 12,
                left: 16,
                zIndex: 15,
                fontSize: 12,
                fontWeight: 500,
                color: "var(--text-3)",
                background: "var(--bg-glass)",
                padding: "4px 10px",
                borderRadius: 999,
                backdropFilter: "blur(10px)",
                pointerEvents: "none",
              }}
            >
              {currentQ ? `第 ${currentQ.number} 题专属草稿纸 · 自动本地保存` : "整卷草稿演算纸 · 自动本地保存"}
            </div>

            <ScratchpadCanvas
              storageKey={`${activeQid}:scratch`}
              dark={dark}
              transparent={false}
              interactive
              showDock
              onHasStrokesChange={handleStrokePresence("scratch")}
            />
          </section>
        )}
      </div>
    </div>
  );
}
