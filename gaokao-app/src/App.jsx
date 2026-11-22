import React, { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";
import LibraryView from "./components/LibraryView";
import PracticeWorkspace from "./components/PracticeWorkspace";
import { loadAllProgress } from "./utils/storage";
import { bankUrl } from "./utils/paths";

export default function App() {
  const [indexData, setIndexData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [progressMap, setProgressMap] = useState({});
  const [dark, setDark] = useState(false);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    fetch(bankUrl("index.json"))
      .then((r) => {
        if (!r.ok) throw new Error(`加载题库索引失败 (HTTP ${r.status})`);
        return r.json();
      })
      .then((data) => {
        setIndexData(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });

    loadAllProgress().then((list) => {
      const m = {};
      for (const item of list) m[item.paperId] = item;
      setProgressMap(m);
    });
  }, []);

  const handleProgressUpdated = (prog) => {
    setProgressMap((prev) => ({ ...prev, [prog.paperId]: prog }));
  };

  if (selectedPaper) {
    return (
      <PracticeWorkspace
        paperMeta={selectedPaper}
        dark={dark}
        onToggleDark={() => setDark((d) => !d)}
        onBack={() => setSelectedPaper(null)}
        onProgressUpdated={handleProgressUpdated}
      />
    );
  }

  return (
    <div>
      <header className="apple-navbar">
        <div className="brand-pill">
          <div className="brand-icon">E</div>
          <span>Evan的试卷库</span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 12.5, color: "var(--text-2)" }}>
            2018–2026 全国无文理综真题 · 开源公益
          </span>
          <button className="icon-btn" onClick={() => setDark((d) => !d)}>
            {dark ? <Sun size={15} /> : <Moon size={15} />}
          </button>
        </div>
      </header>

      {loading ? (
        <div style={{ textAlign: "center", padding: 80, color: "var(--text-2)" }}>正在读取 3,123 份真题索引...</div>
      ) : error ? (
        <div style={{ textAlign: "center", padding: 80, color: "var(--red)" }}>{error}</div>
      ) : (
        <LibraryView
          indexData={indexData}
          progressMap={progressMap}
          onSelectPaper={setSelectedPaper}
        />
      )}
    </div>
  );
}
