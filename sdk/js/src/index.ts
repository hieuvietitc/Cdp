import { getAnonymousId, getUserId, setUserId, getConsent, setConsent, reset } from "./identity";
import { Transport } from "./transport";

interface CDPOptions {
  collectorUrl?: string;
  autoPage?: boolean;
  requireConsent?: boolean;
}

interface ConsentOptions {
  analytics: boolean;
  marketing?: boolean;
}

class CDP {
  private writeKey = "";
  private transport: Transport | null = null;
  private options: CDPOptions = {};
  private _consentGranted = false;

  load(writeKey: string, options: CDPOptions = {}): void {
    this.writeKey = writeKey;
    this.options = {
      collectorUrl: "https://collect.localhost",
      autoPage: true,
      requireConsent: false,
      ...options,
    };
    this._consentGranted = !this.options.requireConsent || getConsent();
    this.transport = new Transport(this.options.collectorUrl!, writeKey);

    if (this.options.autoPage) {
      this.page();
      this._patchHistory();
    }
  }

  track(event: string, properties: Record<string, unknown> = {}): void {
    if (!this._shouldTrack()) return;
    this.transport!.enqueue({
      event_type: "track",
      event,
      anonymous_id: getAnonymousId(),
      user_id: getUserId(),
      properties,
      context: this._buildContext(),
      timestamp: new Date().toISOString(),
    });
  }

  page(properties: Record<string, unknown> = {}): void {
    if (!this._shouldTrack()) return;
    this.transport!.enqueue({
      event_type: "page",
      event: "Page View",
      anonymous_id: getAnonymousId(),
      user_id: getUserId(),
      url: location.href,
      title: document.title,
      referrer: document.referrer,
      properties,
      context: this._buildContext(),
      timestamp: new Date().toISOString(),
    });
  }

  identify(userId: string, traits: Record<string, unknown> = {}): void {
    if (!this._shouldTrack()) return;
    const prevAnon = getAnonymousId();
    setUserId(userId);
    this.transport!.enqueue({
      event_type: "identify",
      event: "Identify",
      anonymous_id: prevAnon,
      user_id: userId,
      traits,
      context: this._buildContext(),
      timestamp: new Date().toISOString(),
    });
  }

  consent(options: ConsentOptions): void {
    this._consentGranted = options.analytics;
    setConsent(options.analytics);
    if (options.analytics) {
      this.page();
    }
  }

  reset(): void {
    reset();
  }

  private _shouldTrack(): boolean {
    if (!this.transport) return false;
    if (this.options.requireConsent && !this._consentGranted) return false;
    return true;
  }

  private _buildContext(): Record<string, unknown> {
    return {
      page: {
        url: location.href,
        title: document.title,
        referrer: document.referrer,
      },
      locale: navigator.language,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      screen: { width: screen.width, height: screen.height },
      user_agent: navigator.userAgent,
      sdk_version: "1.0.0",
    };
  }

  private _patchHistory(): void {
    const originalPush = history.pushState.bind(history);
    history.pushState = (...args) => {
      originalPush(...args);
      this.page();
    };
    window.addEventListener("popstate", () => this.page());
  }
}

const cdpInstance = new CDP();
export default cdpInstance;

// Allow global usage: window.cdp.track(...)
if (typeof window !== "undefined") {
  (window as unknown as Record<string, unknown>).cdp = cdpInstance;
}
