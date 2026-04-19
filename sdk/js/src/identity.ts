const ANON_KEY = "_cdp_anon";
const USER_KEY = "_cdp_uid";
const CONSENT_KEY = "_cdp_consent";

function generateUUID(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

function setCookie(name: string, value: string, days: number): void {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${value}; expires=${expires}; path=/; SameSite=Lax`;
}

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
  return match ? decodeURIComponent(match[1]) : null;
}

export function getAnonymousId(): string {
  let id = localStorage.getItem(ANON_KEY) || getCookie(ANON_KEY);
  if (!id) {
    id = generateUUID();
    localStorage.setItem(ANON_KEY, id);
    setCookie(ANON_KEY, id, 365);
  }
  return id;
}

export function getUserId(): string | null {
  return localStorage.getItem(USER_KEY);
}

export function setUserId(userId: string): void {
  localStorage.setItem(USER_KEY, userId);
}

export function getConsent(): boolean {
  const val = localStorage.getItem(CONSENT_KEY);
  return val === "true";
}

export function setConsent(granted: boolean): void {
  localStorage.setItem(CONSENT_KEY, String(granted));
}

export function reset(): void {
  localStorage.removeItem(ANON_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(CONSENT_KEY);
  // Clear cookies
  document.cookie = `${ANON_KEY}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/`;
}
