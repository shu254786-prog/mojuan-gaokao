const DB_NAME = "gaokao_studio_db";
const DB_VERSION = 1;

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains("strokes")) {
        db.createObjectStore("strokes", { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains("progress")) {
        db.createObjectStore("progress", { keyPath: "paperId" });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

export async function loadStrokes(key) {
  try {
    const db = await openDB();
    return await new Promise((resolve) => {
      const tx = db.transaction("strokes", "readonly");
      const req = tx.objectStore("strokes").get(key);
      req.onsuccess = () => resolve(req.result?.strokes || []);
      req.onerror = () => resolve([]);
    });
  } catch {
    return [];
  }
}

export async function saveStrokes(key, strokes) {
  try {
    const db = await openDB();
    await new Promise((resolve, reject) => {
      const tx = db.transaction("strokes", "readwrite");
      tx.objectStore("strokes").put({ id: key, strokes, updatedAt: Date.now() });
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch {
    // ignore storage quota errors gracefully
  }
}

export async function loadAllStrokeKeys() {
  try {
    const db = await openDB();
    return await new Promise((resolve) => {
      const tx = db.transaction("strokes", "readonly");
      const req = tx.objectStore("strokes").getAll();
      req.onsuccess = () => {
        const keys = new Set();
        for (const item of req.result || []) {
          if (item.strokes && item.strokes.length > 0) {
            keys.add(item.id);
          }
        }
        resolve(keys);
      };
      req.onerror = () => resolve(new Set());
    });
  } catch {
    return new Set();
  }
}

export async function loadPaperProgress(paperId) {
  try {
    const db = await openDB();
    return await new Promise((resolve) => {
      const tx = db.transaction("progress", "readonly");
      const req = tx.objectStore("progress").get(paperId);
      req.onsuccess = () => resolve(req.result || { paperId, answers: {}, results: {}, wrongQids: [] });
      req.onerror = () => resolve({ paperId, answers: {}, results: {}, wrongQids: [] });
    });
  } catch {
    return { paperId, answers: {}, results: {}, wrongQids: [] };
  }
}

export async function savePaperProgress(data) {
  try {
    const db = await openDB();
    await new Promise((resolve, reject) => {
      const tx = db.transaction("progress", "readwrite");
      tx.objectStore("progress").put({ ...data, updatedAt: Date.now() });
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch {
    // ignore
  }
}

export async function loadAllProgress() {
  try {
    const db = await openDB();
    return await new Promise((resolve) => {
      const tx = db.transaction("progress", "readonly");
      const req = tx.objectStore("progress").getAll();
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => resolve([]);
    });
  } catch {
    return [];
  }
}
