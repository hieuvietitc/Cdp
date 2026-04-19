const MAX_QUEUE_SIZE = 20;
const FLUSH_INTERVAL_MS = 5000;
const MAX_RETRIES = 3;

export interface EventPayload {
  [key: string]: unknown;
}

export class Transport {
  private queue: EventPayload[] = [];
  private flushTimer: ReturnType<typeof setInterval> | null = null;
  private collectorUrl: string;
  private writeKey: string;

  constructor(collectorUrl: string, writeKey: string) {
    this.collectorUrl = collectorUrl.replace(/\/$/, "");
    this.writeKey = writeKey;
    this.startFlushTimer();
    this.bindUnloadHandler();
  }

  enqueue(event: EventPayload): void {
    this.queue.push(event);
    if (this.queue.length >= MAX_QUEUE_SIZE) {
      this.flush();
    }
  }

  flush(): void {
    if (this.queue.length === 0) return;
    const batch = this.queue.splice(0);
    this.sendBatch(batch, 0);
  }

  private sendBatch(batch: EventPayload[], attempt: number): void {
    const url = `${this.collectorUrl}/v1/events/batch`;
    const body = JSON.stringify({ write_key: this.writeKey, batch });

    if (typeof navigator !== "undefined" && navigator.sendBeacon) {
      const blob = new Blob([body], { type: "application/json" });
      const ok = navigator.sendBeacon(url, blob);
      if (ok) return;
    }

    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      keepalive: true,
    })
      .then((res) => {
        if (!res.ok && attempt < MAX_RETRIES) {
          this.retryBatch(batch, attempt);
        }
      })
      .catch(() => {
        if (attempt < MAX_RETRIES) {
          this.retryBatch(batch, attempt);
        }
      });
  }

  private retryBatch(batch: EventPayload[], attempt: number): void {
    const delay = Math.pow(2, attempt) * 1000;
    setTimeout(() => this.sendBatch(batch, attempt + 1), delay);
  }

  private startFlushTimer(): void {
    this.flushTimer = setInterval(() => this.flush(), FLUSH_INTERVAL_MS);
  }

  private bindUnloadHandler(): void {
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "hidden") {
        this.flush();
      }
    });
  }

  destroy(): void {
    if (this.flushTimer) clearInterval(this.flushTimer);
  }
}
