import { TranscriptUpdate, CallSession } from "@/lib/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://127.0.0.1:8000";

type WebSocketCallback = (data: TranscriptUpdate) => void;

class WebSocketManager {
  private ws: WebSocket | null = null;
  private sessionId: number | null = null;
  private callbacks: Set<WebSocketCallback> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;

  connect(sessionId: number): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }
      
      // Don't create multiple connections if already connecting
      if (this.ws?.readyState === WebSocket.CONNECTING && this.sessionId === sessionId) {
        return;
      }

      this.sessionId = sessionId;
      const url = `${WS_URL}/ws/calls/${sessionId}`;

      try {
        const ws = new WebSocket(url);
        this.ws = ws;

        ws.onopen = () => {
          if (this.ws !== ws) return; // Ignore if replaced
          console.log("WebSocket connected");
          this.reconnectAttempts = 0;
          resolve();
        };

        ws.onmessage = (event) => {
          if (this.ws !== ws) return;
          try {
            const data = JSON.parse(event.data) as TranscriptUpdate;
            this.callbacks.forEach((cb) => cb(data));
          } catch (error) {
            console.error("Failed to parse WebSocket message:", error);
          }
        };

        ws.onclose = () => {
          if (this.ws !== ws) return; // Only trigger reconnect if this is the active socket
          console.log("WebSocket disconnected");
          this.attemptReconnect();
        };

        ws.onerror = (error) => {
          if (this.ws !== ws) {
            // Intentionally aborted during fast navigation or StrictMode
            return;
          }
          console.error("WebSocket error:", error);
          if (this.reconnectAttempts === 0) {
            reject(error);
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private attemptReconnect(): void {
    if (
      this.sessionId &&
      this.reconnectAttempts < this.maxReconnectAttempts
    ) {
      this.reconnectAttempts++;
      console.log(
        `Attempting reconnect ${this.reconnectAttempts}/${this.maxReconnectAttempts}`
      );
      setTimeout(() => {
        if (this.sessionId) {
          this.connect(this.sessionId).catch(() => {});
        }
      }, 1000 * this.reconnectAttempts);
    }
  }

  disconnect(): void {
    if (this.ws) {
      if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
        this.ws.close();
      }
      this.ws = null;
      this.sessionId = null;
    }
  }

  subscribe(callback: WebSocketCallback): () => void {
    this.callbacks.add(callback);
    return () => {
      this.callbacks.delete(callback);
    };
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsManager = new WebSocketManager();