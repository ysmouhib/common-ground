// The reviewer token lives in sessionStorage: it is gone when the tab closes and is
// never written to disk-backed storage or to a cookie. It is sent only as an
// Authorization header to this site's own API.
const KEY = "common-ground.reviewer-token";

export function getReviewerToken(): string {
  try {
    return window.sessionStorage.getItem(KEY) ?? "";
  } catch {
    return "";
  }
}

export function setReviewerToken(token: string): void {
  try {
    if (token) window.sessionStorage.setItem(KEY, token);
    else window.sessionStorage.removeItem(KEY);
  } catch {
    // Storage is unavailable (private mode, blocked): the session simply stays read-only.
  }
}
