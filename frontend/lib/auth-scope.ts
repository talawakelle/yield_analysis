
export type ExternalScopeIdentity = {
  username: string | null;
  source: string;
};

const STORAGE_KEY = "plantation.external.auth";
const QUERY_KEYS = ["username", "user", "email", "login"];

function readStorage(key: string): string | null {
  try {
    return window.localStorage.getItem(key) || window.sessionStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStorage(key: string, value: string) {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // ignore storage failures
  }
}

function removeStorage(key: string) {
  try {
    window.localStorage.removeItem(key);
    window.sessionStorage.removeItem(key);
  } catch {
    // ignore storage failures
  }
}

function extractUsernameFromUnknown(value: unknown): string | null {
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) return null;
    if ((trimmed.startsWith("{") && trimmed.endsWith("}")) || (trimmed.startsWith("[") && trimmed.endsWith("]"))) {
      try {
        return extractUsernameFromUnknown(JSON.parse(trimmed));
      } catch {
        return trimmed;
      }
    }
    return trimmed;
  }

  if (Array.isArray(value)) {
    for (const item of value) {
      const resolved = extractUsernameFromUnknown(item);
      if (resolved) return resolved;
    }
    return null;
  }

  if (value && typeof value === "object") {
    const record = value as Record<string, unknown>;
    const candidateKeys = ["username", "user", "login", "email", "name", "currentUser"];
    for (const key of candidateKeys) {
      const resolved = extractUsernameFromUnknown(record[key]);
      if (resolved) return resolved;
    }
  }

  return null;
}

export function getExternalScopeIdentity(): ExternalScopeIdentity {
  if (typeof window === "undefined") return { username: null, source: "server" };

  const params = new URLSearchParams(window.location.search);
  for (const key of QUERY_KEYS) {
    const value = params.get(key)?.trim();
    if (value) return { username: value, source: `query:${key}` };
  }

  const raw = readStorage(STORAGE_KEY);
  const stored = extractUsernameFromUnknown(raw);
  if (stored) return { username: stored, source: `storage:${STORAGE_KEY}` };

  return { username: null, source: "anonymous" };
}

export function persistExternalScopeIdentity() {
  if (typeof window === "undefined") return;
  const identity = getExternalScopeIdentity();
  if (identity.username) {
    writeStorage(STORAGE_KEY, JSON.stringify({ username: identity.username }));
  }
}

export function clearExternalScopeIdentity() {
  if (typeof window === "undefined") return;
  removeStorage(STORAGE_KEY);
}
