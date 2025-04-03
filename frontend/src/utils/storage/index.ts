/**
 * 本地存储封装
 */

interface Storage {
  get<T>(key: string): T | null;
  set<T>(key: string, value: T): void;
  remove(key: string): void;
  clear(): void;
}

class LocalStorage implements Storage {
  private prefix: string;

  constructor(prefix = 'app_') {
    this.prefix = prefix;
  }

  private getKey(key: string): string {
    return `${this.prefix}${key}`;
  }

  get<T>(key: string): T | null {
    const value = localStorage.getItem(this.getKey(key));
    if (value) {
      try {
        return JSON.parse(value) as T;
      } catch {
        return null;
      }
    }
    return null;
  }

  set<T>(key: string, value: T): void {
    localStorage.setItem(this.getKey(key), JSON.stringify(value));
  }

  remove(key: string): void {
    localStorage.removeItem(this.getKey(key));
  }

  clear(): void {
    localStorage.clear();
  }
}

class SessionStorageClass implements Storage {
  private prefix: string;

  constructor(prefix = 'app_') {
    this.prefix = prefix;
  }

  private getKey(key: string): string {
    return `${this.prefix}${key}`;
  }

  get<T>(key: string): T | null {
    const value = window.sessionStorage.getItem(this.getKey(key));
    if (value) {
      try {
        return JSON.parse(value) as T;
      } catch {
        return null;
      }
    }
    return null;
  }

  set<T>(key: string, value: T): void {
    window.sessionStorage.setItem(this.getKey(key), JSON.stringify(value));
  }

  remove(key: string): void {
    window.sessionStorage.removeItem(this.getKey(key));
  }

  clear(): void {
    window.sessionStorage.clear();
  }
}

export const storage = new LocalStorage();
export const sessionStorage = new SessionStorageClass();
