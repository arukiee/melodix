import type { SearchResult } from '../api/search';

const HISTORY_KEY = 'melodix_search_history';
const CACHE_KEY = 'melodix_search_cache';

export class SearchHistoryManager {
  static getRecentSearches(): string[] {
    try {
      const data = localStorage.getItem(HISTORY_KEY);
      return data ? JSON.parse(data) : [];
    } catch {
      return [];
    }
  }

  static addSearchTerm(term: string) {
    if (!term.trim()) return;
    try {
      let history = this.getRecentSearches();
      history = history.filter(t => t.toLowerCase() !== term.toLowerCase());
      history.unshift(term.trim());
      if (history.length > 10) history.pop();
      localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    } catch (e) {
      console.warn("Failed to save search history", e);
    }
  }

  static cacheResults(query: string, results: SearchResult[]) {
    const q = query.trim().toLowerCase();
    if (!q || !results || results.length === 0) return;
    try {
      let cache: Record<string, { timestamp: number; results: SearchResult[] }> = {};
      const raw = localStorage.getItem(CACHE_KEY);
      if (raw) cache = JSON.parse(raw);
      
      cache[q] = {
        timestamp: Date.now(),
        results: results.slice(0, 20) // Only cache top 20
      };
      
      // Cleanup old cache entries if > 50
      const keys = Object.keys(cache);
      if (keys.length > 50) {
        const oldest = keys.sort((a, b) => cache[a].timestamp - cache[b].timestamp)[0];
        delete cache[oldest];
      }
      
      localStorage.setItem(CACHE_KEY, JSON.stringify(cache));
    } catch (e) {
      console.warn("Failed to cache search results", e);
    }
  }

  static getCachedResults(query: string): SearchResult[] | null {
    const q = query.trim().toLowerCase();
    if (!q) return null;
    try {
      const raw = localStorage.getItem(CACHE_KEY);
      if (!raw) return null;
      
      const cache = JSON.parse(raw);
      const entry = cache[q];
      
      // Expire cache after 24 hours, and only return valid non-empty arrays
      if (entry && Array.isArray(entry.results) && entry.results.length > 0 && (Date.now() - entry.timestamp < 24 * 60 * 60 * 1000)) {
        return entry.results;
      }
      return null;
    } catch {
      return null;
    }
  }

  static clearCache() {
    try {
      localStorage.removeItem(CACHE_KEY);
    } catch (e) {
      console.warn("Failed to clear search cache", e);
    }
  }
}
