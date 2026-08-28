type Callback = (data: any) => void;

export class JarvisWebSocket {
  private ws: WebSocket | null = null;
  private listeners: Set<Callback> = new Set();
  private onStatusChange: (connected: boolean) => void;

  constructor(onStatusChange: (connected: boolean) => void) {
    this.onStatusChange = onStatusChange;
  }

  connect() {
    this.ws = new WebSocket('ws://localhost:8000/ws/jarvis');

    this.ws.onopen = () => {
      console.log('WS Connected');
      this.onStatusChange(true);
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.listeners.forEach((listener) => listener(data));
      } catch (e) {
        console.error('Failed to parse WS message', e);
      }
    };

    this.ws.onclose = () => {
      console.log('WS Disconnected');
      this.onStatusChange(false);
      setTimeout(() => this.connect(), 3000); // Reconnect attempt
    };
  }

  subscribe(callback: Callback) {
    this.listeners.add(callback);
    return () => { this.listeners.delete(callback); };
  }

  send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.close();
      this.ws = null;
    }
  }
}
