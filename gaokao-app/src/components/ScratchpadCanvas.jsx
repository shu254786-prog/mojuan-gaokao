import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Eraser,
  Highlighter,
  Minus,
  PenTool,
  Redo2,
  Hand,
  Trash2,
  Undo2,
  Grid3X3,
} from "lucide-react";
import { loadStrokes, saveStrokes } from "../utils/storage";

const COLORS = [
  { id: "ink", value: "#1D1D1F", darkValue: "#F5F5F7", label: "曜石黑" },
  { id: "blue", value: "#0071E3", darkValue: "#0A84FF", label: "苹果蓝" },
  { id: "red", value: "#FF3B30", darkValue: "#FF453A", label: "批改红" },
  { id: "green", value: "#248A3D", darkValue: "#30D158", label: "标注绿" },
  { id: "orange", value: "#E07B00", darkValue: "#FF9F0A", label: "重点橙" },
];

const WIDTHS = [
  { id: "fine", value: 2.0, dot: 5 },
  { id: "med", value: 3.4, dot: 8 },
  { id: "bold", value: 5.5, dot: 12 },
];

const PAPER_STYLES = [
  { id: "dot", label: "点阵" },
  { id: "grid", label: "方格" },
  { id: "lined", label: "横线" },
  { id: "blank", label: "纯白" },
];

function distToSegment(px, py, x1, y1, x2, y2) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const lenSq = dx * dx + dy * dy;
  if (lenSq === 0) return Math.hypot(px - x1, py - y1);
  let t = ((px - x1) * dx + (py - y1) * dy) / lenSq;
  t = Math.max(0, Math.min(1, t));
  return Math.hypot(px - (x1 + t * dx), py - (y1 + t * dy));
}

function strokeHitTest(stroke, px, py, radius = 14) {
  const pts = stroke.points;
  if (!pts || pts.length === 0) return false;
  if (pts.length === 1) return Math.hypot(px - pts[0].x, py - pts[0].y) <= radius;
  for (let i = 0; i < pts.length - 1; i++) {
    if (distToSegment(px, py, pts[i].x, pts[i].y, pts[i + 1].x, pts[i + 1].y) <= radius) {
      return true;
    }
  }
  return false;
}

function resolveColor(colorId, dark) {
  const found = COLORS.find((c) => c.id === colorId);
  if (!found) return dark ? "#F5F5F7" : "#1D1D1F";
  return dark ? found.darkValue : found.value;
}

function drawStroke(ctx, stroke, dark) {
  const pts = stroke.points;
  if (!pts || pts.length === 0) return;

  ctx.save();
  ctx.lineCap = "round";
  ctx.lineJoin = "round";

  const color = resolveColor(stroke.colorId, dark);
  ctx.strokeStyle = color;
  ctx.fillStyle = color;

  if (stroke.tool === "highlighter") {
    ctx.globalAlpha = 0.28;
    ctx.lineWidth = stroke.width * 4.5;
  } else if (stroke.tool === "line") {
    ctx.globalAlpha = 0.92;
    ctx.lineWidth = stroke.width;
  } else {
    ctx.globalAlpha = 1;
    ctx.lineWidth = stroke.width;
  }

  if (stroke.tool === "line" && pts.length >= 2) {
    const a = pts[0];
    const b = pts[pts.length - 1];
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.stroke();
    ctx.restore();
    return;
  }

  if (pts.length === 1) {
    ctx.beginPath();
    ctx.arc(pts[0].x, pts[0].y, ctx.lineWidth * 0.5, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
    return;
  }

  // Smooth quadratic Bezier midpoint curve with optional pen pressure
  if (stroke.tool === "pen" && stroke.hasPressure) {
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[i];
      const p1 = pts[i + 1];
      const press = ((p0.p ?? 0.5) + (p1.p ?? 0.5)) * 0.5;
      ctx.lineWidth = Math.max(1.0, stroke.width * (0.45 + press * 1.1));
      ctx.beginPath();
      ctx.moveTo(p0.x, p0.y);
      ctx.lineTo(p1.x, p1.y);
      ctx.stroke();
    }
  } else {
    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    for (let i = 1; i < pts.length - 1; i++) {
      const midX = (pts[i].x + pts[i + 1].x) * 0.5;
      const midY = (pts[i].y + pts[i + 1].y) * 0.5;
      ctx.quadraticCurveTo(pts[i].x, pts[i].y, midX, midY);
    }
    const last = pts[pts.length - 1];
    ctx.lineTo(last.x, last.y);
    ctx.stroke();
  }
  ctx.restore();
}

export default function ScratchpadCanvas({
  storageKey,
  dark = false,
  transparent = false,
  interactive = true,
  showDock = true,
  onHasStrokesChange,
}) {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);

  const [strokes, setStrokes] = useState([]);
  const [redoStack, setRedoStack] = useState([]);
  const [tool, setTool] = useState("pen"); // pen | highlighter | line | eraser
  const [colorId, setColorId] = useState("ink");
  const [widthIdx, setWidthIdx] = useState(1);
  const [paperStyle, setPaperStyle] = useState("dot");
  const [penOnly, setPenOnly] = useState(false);

  const activeStrokeRef = useRef(null);
  const isDrawingRef = useRef(false);
  const strokesRef = useRef([]);

  useEffect(() => {
    strokesRef.current = strokes;
    onHasStrokesChange?.(strokes.length > 0);
  }, [strokes, onHasStrokesChange]);

  // Load persisted strokes when switching questions
  useEffect(() => {
    let cancelled = false;
    setRedoStack([]);
    activeStrokeRef.current = null;
    isDrawingRef.current = false;
    loadStrokes(storageKey).then((loaded) => {
      if (!cancelled) {
        setStrokes(loaded);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [storageKey]);

  const redraw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    ctx.save();
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, canvas.width / dpr, canvas.height / dpr);
    for (const s of strokesRef.current) {
      drawStroke(ctx, s, dark);
    }
    if (activeStrokeRef.current) {
      drawStroke(ctx, activeStrokeRef.current, dark);
    }
    ctx.restore();
  }, [dark]);

  // ResizeObserver for crisp Retina canvas
  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const updateSize = () => {
      const rect = container.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      const w = Math.max(1, Math.floor(rect.width));
      const h = Math.max(1, Math.floor(rect.height));
      if (canvas.width !== Math.floor(w * dpr) || canvas.height !== Math.floor(h * dpr)) {
        canvas.width = Math.floor(w * dpr);
        canvas.height = Math.floor(h * dpr);
        canvas.style.width = `${w}px`;
        canvas.style.height = `${h}px`;
        redraw();
      }
    };
    updateSize();
    const ro = new ResizeObserver(updateSize);
    ro.observe(container);
    return () => ro.disconnect();
  }, [redraw]);

  useEffect(() => {
    redraw();
  }, [strokes, redraw]);

  const persist = useCallback(
    (next) => {
      setStrokes(next);
      saveStrokes(storageKey, next);
    },
    [storageKey]
  );

  const handleUndo = useCallback(() => {
    setStrokes((prev) => {
      if (prev.length === 0) return prev;
      const last = prev[prev.length - 1];
      const next = prev.slice(0, -1);
      setRedoStack((r) => [...r, last]);
      saveStrokes(storageKey, next);
      return next;
    });
  }, [storageKey]);

  const handleRedo = useCallback(() => {
    setRedoStack((prevRedo) => {
      if (prevRedo.length === 0) return prevRedo;
      const item = prevRedo[prevRedo.length - 1];
      setStrokes((prevS) => {
        const next = [...prevS, item];
        saveStrokes(storageKey, next);
        return next;
      });
      return prevRedo.slice(0, -1);
    });
  }, [storageKey]);

  const handleClear = useCallback(() => {
    if (strokesRef.current.length === 0) return;
    setRedoStack([]);
    persist([]);
  }, [persist]);

  // Keyboard shortcuts Ctrl+Z / Ctrl+Y
  useEffect(() => {
    if (!interactive) return;
    const onKey = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
        if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
        e.preventDefault();
        if (e.shiftKey) handleRedo();
        else handleUndo();
      } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "y") {
        if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
        e.preventDefault();
        handleRedo();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [interactive, handleUndo, handleRedo]);

  const getPt = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
      p: e.pointerType === "pen" ? Math.max(0.1, e.pressure || 0.5) : 0.5,
    };
  };

  const onPointerDown = (e) => {
    if (!interactive) return;
    if (penOnly && e.pointerType === "touch") return;
    if (e.button === 2) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    const pt = getPt(e);
    isDrawingRef.current = true;

    if (tool === "eraser") {
      const hitIdx = strokesRef.current.findIndex((s) => strokeHitTest(s, pt.x, pt.y));
      if (hitIdx !== -1) {
        const next = strokesRef.current.filter((_, idx) => idx !== hitIdx);
        persist(next);
      }
      return;
    }

    activeStrokeRef.current = {
      tool,
      colorId,
      width: WIDTHS[widthIdx].value,
      hasPressure: e.pointerType === "pen",
      points: [pt],
    };
    redraw();
  };

  const onPointerMove = (e) => {
    if (!isDrawingRef.current || !interactive) return;
    if (penOnly && e.pointerType === "touch") return;
    const pt = getPt(e);

    if (tool === "eraser") {
      const filtered = strokesRef.current.filter((s) => !strokeHitTest(s, pt.x, pt.y));
      if (filtered.length !== strokesRef.current.length) {
        persist(filtered);
      }
      return;
    }

    const active = activeStrokeRef.current;
    if (!active) return;

    if (active.tool === "line") {
      const start = active.points[0];
      let endPt = pt;
      // Hold Shift or close to horizontal/vertical to snap auxiliary lines
      if (e.shiftKey) {
        const dx = Math.abs(pt.x - start.x);
        const dy = Math.abs(pt.y - start.y);
        if (dx > dy * 2.5) endPt = { ...pt, y: start.y };
        else if (dy > dx * 2.5) endPt = { ...pt, x: start.x };
      }
      active.points = [start, endPt];
    } else {
      const last = active.points[active.points.length - 1];
      if (Math.hypot(pt.x - last.x, pt.y - last.y) >= 1.5) {
        active.points.push(pt);
      }
    }
    redraw();
  };

  const onPointerUp = (e) => {
    if (!isDrawingRef.current) return;
    isDrawingRef.current = false;
    try {
      e.currentTarget.releasePointerCapture(e.pointerId);
    } catch {
      // ignore
    }
    if (tool !== "eraser" && activeStrokeRef.current) {
      const finished = activeStrokeRef.current;
      activeStrokeRef.current = null;
      setRedoStack([]);
      persist([...strokesRef.current, finished]);
    }
  };

  const cyclePaperStyle = () => {
    const idx = PAPER_STYLES.findIndex((p) => p.id === paperStyle);
    setPaperStyle(PAPER_STYLES[(idx + 1) % PAPER_STYLES.length].id);
  };

  const bgClass = transparent ? "" : `paper-bg-${paperStyle}`;

  return (
    <div
      ref={containerRef}
      className={bgClass}
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        touchAction: interactive ? (transparent && penOnly ? "pan-y" : "none") : "auto",
        userSelect: "none",
      }}
    >
      <canvas
        ref={canvasRef}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        style={{
          display: "block",
          width: "100%",
          height: "100%",
          cursor: interactive ? (tool === "eraser" ? "cell" : "crosshair") : "default",
        }}
      />

      {showDock && interactive && (
        <div className="pencil-dock" role="toolbar" aria-label="平板画笔工具栏">
          <button
            className={`dock-tool ${tool === "pen" ? "active" : ""}`}
            onClick={() => setTool("pen")}
            title="钢笔 (流畅手写)"
          >
            <PenTool size={16} />
          </button>
          <button
            className={`dock-tool ${tool === "highlighter" ? "active" : ""}`}
            onClick={() => setTool("highlighter")}
            title="荧光标记笔"
          >
            <Highlighter size={16} />
          </button>
          <button
            className={`dock-tool ${tool === "line" ? "active" : ""}`}
            onClick={() => setTool("line")}
            title="几何辅助直尺 (按住Shift对齐水平/垂直)"
          >
            <Minus size={16} style={{ transform: "rotate(-35deg)" }} />
          </button>
          <button
            className={`dock-tool ${tool === "eraser" ? "active" : ""}`}
            onClick={() => setTool("eraser")}
            title="笔画橡皮擦"
          >
            <Eraser size={16} />
          </button>

          <div className="dock-sep" />

          {COLORS.map((c) => (
            <button
              key={c.id}
              className={`color-swatch ${colorId === c.id ? "active" : ""}`}
              style={{ background: dark ? c.darkValue : c.value }}
              onClick={() => {
                setColorId(c.id);
                if (tool === "eraser") setTool("pen");
              }}
              title={c.label}
            />
          ))}

          <div className="dock-sep" />

          {WIDTHS.map((w, idx) => (
            <button
              key={w.id}
              className={`width-dot-btn ${widthIdx === idx ? "active" : ""}`}
              onClick={() => setWidthIdx(idx)}
              title="笔触粗细"
            >
              <span className="width-dot" style={{ width: w.dot, height: w.dot }} />
            </button>
          ))}

          <div className="dock-sep" />

          <button
            className="dock-tool"
            onClick={handleUndo}
            disabled={strokes.length === 0}
            title="撤销 (Ctrl+Z)"
          >
            <Undo2 size={16} />
          </button>
          <button
            className="dock-tool"
            onClick={handleRedo}
            disabled={redoStack.length === 0}
            title="重做 (Ctrl+Y)"
          >
            <Redo2 size={16} />
          </button>

          {!transparent && (
            <button
              className="dock-tool"
              onClick={cyclePaperStyle}
              title={`切换纸张底纹 (当前: ${PAPER_STYLES.find((p) => p.id === paperStyle)?.label})`}
            >
              <Grid3X3 size={16} />
            </button>
          )}

          <button
            className={`dock-tool ${penOnly ? "active" : ""}`}
            onClick={() => setPenOnly((v) => !v)}
            title={penOnly ? "防误触已开启：仅响应手写笔/鼠标" : "开启防误触（忽略手指触碰）"}
          >
            <Hand size={16} />
          </button>

          <button
            className="dock-tool"
            onClick={handleClear}
            disabled={strokes.length === 0}
            title="清空当前草稿"
          >
            <Trash2 size={16} />
          </button>
        </div>
      )}
    </div>
  );
}
