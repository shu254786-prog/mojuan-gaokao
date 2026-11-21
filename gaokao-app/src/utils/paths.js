const BASE = import.meta.env.BASE_URL || "/";
const BANK_BASE = (import.meta.env.VITE_BANK_BASE || `${BASE}bank`).replace(/\/+$/, "");
const COLLECTED_BASE = (import.meta.env.VITE_COLLECTED_BASE || `${BASE}collected`).replace(/\/+$/, "");

export function bankUrl(relPath) {
  if (!relPath) return "";
  if (/^https?:\/\//i.test(relPath)) return relPath;
  const clean = relPath.replace(/^\/?(?:bank\/)+/, "").replace(/^\/+/, "");
  return `${BANK_BASE}/${clean}`;
}

export function collectedUrl(relPath) {
  if (!relPath) return "";
  if (/^https?:\/\//i.test(relPath)) return relPath;
  const clean = relPath
    .replace(/^\.\.\/collected\//, "")
    .replace(/^\/?(?:collected\/)+/, "")
    .replace(/^\/+/, "");
  return `${COLLECTED_BASE}/${clean}`;
}
