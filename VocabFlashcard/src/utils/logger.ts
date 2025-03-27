type LogLevel = "info" | "error" | "warn";

class BrowserLogger {
  private logToFile(level: LogLevel, message: string) {
    const timestamp = new Date().toISOString();
    const logMessage = `${timestamp} ${level}: ${message}`;

    // Log to console for development
    console[level](logMessage);

    // Store in localStorage for persistence (optional)
    if (typeof localStorage !== "undefined") {
      const logs = JSON.parse(localStorage.getItem("app_logs") || "[]");
      logs.push(logMessage);
      localStorage.setItem("app_logs", JSON.stringify(logs.slice(-1000))); // Keep last 1000 logs
    }
  }

  info(message: string) {
    this.logToFile("info", message);
  }

  error(message: string) {
    this.logToFile("error", message);
  }

  warn(message: string) {
    this.logToFile("warn", message);
  }
}

class ServerLogger {
  info(message: string) {
    const timestamp = new Date().toISOString();
    console.log(`${timestamp} info: ${message}`);
  }

  error(message: string) {
    const timestamp = new Date().toISOString();
    console.error(`${timestamp} error: ${message}`);
  }

  warn(message: string) {
    const timestamp = new Date().toISOString();
    console.warn(`${timestamp} warn: ${message}`);
  }
}

export const logger =
  typeof window === "undefined" ? new ServerLogger() : new BrowserLogger();
