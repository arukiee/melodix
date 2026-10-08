import React, { useState, useEffect, useRef } from 'react';
import { Search, Loader, Clock, X, Music } from 'lucide-react';
import { searchApi, type SearchResult } from '../../api/search';
import { SearchHistoryManager } from '../../services/SearchHistoryManager';
import { SongDetailModal } from './SongDetailModal';

export const UniversalSearch: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSong, setSelectedSong] = useState<SearchResult | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const debounceTimerRef = useRef<any>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const executeSearch = async (searchQuery: string) => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    const trimmed = searchQuery.trim();
    if (!trimmed) {
      setResults([]);
      setError(null);
      return;
    }

    // Cancel any existing in-flight request to avoid race conditions or duplicate network execution
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setLoading(true);
    setIsOpen(true);
    setError(null);
    try {
      const cached = SearchHistoryManager.getCachedResults(trimmed);
      if (cached && cached.length > 0) {
        setResults(cached);
      } else {
        const res = await searchApi.searchSongs(trimmed, {}, controller.signal);
        const validResults = res || [];
        setResults(validResults);
        if (validResults.length > 0) {
          SearchHistoryManager.cacheResults(trimmed, validResults);
        }
      }
      SearchHistoryManager.addSearchTerm(trimmed);
    } catch (err: any) {
      if (err?.name === 'CanceledError' || err?.code === 'ERR_CANCELED') {
        // Aborted request, do not update error state
        return;
      }
      console.error("Search failed:", err);
      setError(err?.response?.data?.detail || err?.message || "Search failed");
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleQueryChange = (val: string) => {
    setQuery(val);
    setIsOpen(true);

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    if (!val.trim()) {
      setResults([]);
      return;
    }

    debounceTimerRef.current = setTimeout(() => {
      executeSearch(val);
    }, 500);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    executeSearch(query);
  };

  // Handle outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  const recentSearches = SearchHistoryManager.getRecentSearches();

  return (
    <div ref={containerRef} style={{ position: 'relative', width: '100%', maxWidth: '600px', margin: '0 auto' }}>
      <form onSubmit={handleSubmit} style={{
        display: 'flex',
        alignItems: 'center',
        background: 'var(--surface-color)',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-button)',
        padding: '0 16px',
        height: '48px',
        transition: 'all 0.2s ease',
        boxShadow: isOpen ? '0 4px 12px rgba(0,0,0,0.1)' : 'none',
      }}>
        <button
          type="submit"
          style={{
            background: 'none',
            border: 'none',
            padding: 0,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
          title="Search"
        >
          <Search size={20} color="var(--text-secondary)" />
        </button>
        <input
          type="text"
          value={query}
          onChange={(e) => handleQueryChange(e.target.value)}
          onFocus={() => setIsOpen(true)}
          placeholder="Search for a song, artist, or composer..."
          style={{
            flex: 1,
            background: 'none',
            border: 'none',
            outline: 'none',
            color: 'var(--text-primary)',
            padding: '0 12px',
            fontSize: '1rem'
          }}
        />
        {loading && <Loader size={18} className="spin" color="var(--accent-primary)" />}
        {query && !loading && (
          <X size={18} style={{ cursor: 'pointer', color: 'var(--text-secondary)' }} onClick={() => { setQuery(''); setResults([]); }} />
        )}
      </form>

      {isOpen && (
        <div style={{
          position: 'absolute',
          top: '56px',
          left: 0,
          right: 0,
          background: 'var(--surface-color)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-card)',
          boxShadow: 'var(--shadow-lg)',
          zIndex: 100,
          maxHeight: '400px',
          overflowY: 'auto'
        }}>
          {!query.trim() && recentSearches.length > 0 && (
            <div style={{ padding: '12px' }}>
              <h4 style={{ margin: '0 0 8px 8px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Recent Searches</h4>
              {recentSearches.map(term => (
                <div 
                  key={term}
                  onClick={() => { setQuery(term); executeSearch(term); }}
                  style={{
                    display: 'flex', alignItems: 'center', padding: '10px',
                    cursor: 'pointer', borderRadius: '4px', gap: '8px'
                  }}
                  className="hover-bg-light"
                >
                  <Clock size={16} color="var(--text-secondary)" />
                  <span>{term}</span>
                </div>
              ))}
            </div>
          )}

          {error && !loading && (
            <div style={{ padding: '16px 20px', color: '#f87171', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '8px', margin: '12px', fontSize: '0.85rem', lineHeight: '1.4' }}>
              ⚠️ {error}
            </div>
          )}

          {query.trim() && results.length === 0 && !loading && !error && (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>
              No results found for "{query}"
            </div>
          )}

          {results.length > 0 && (
            <div style={{ padding: '8px 0' }}>
              {results.map((res, index) => (
                <div
                  key={`${res.id}-${index}`}
                  onClick={() => {
                    setSelectedSong(res);
                    setIsOpen(false);
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '10px 16px',
                    cursor: 'pointer',
                    borderBottom: '1px solid var(--border-color)',
                  }}
                  className="hover-bg-light"
                >
                  {res.thumbnailUrl ? (
                    <img
                      src={res.thumbnailUrl}
                      alt={res.title}
                      style={{ width: '44px', height: '44px', objectFit: 'cover', borderRadius: '4px', flexShrink: 0 }}
                    />
                  ) : (
                    <div style={{ width: '44px', height: '44px', background: 'var(--bg-color)', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <Music size={20} color="var(--text-secondary)" />
                    </div>
                  )}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: '600', fontSize: '0.95rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {res.title}
                    </div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginTop: '2px' }}>
                      <span>{res.artist}</span>
                      {res.duration && (
                        <>
                          <span> • </span>
                          <span>{Math.floor(res.duration / 60)}:{(res.duration % 60).toString().padStart(2, '0')}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {selectedSong && (
        <SongDetailModal 
          song={selectedSong} 
          onClose={() => setSelectedSong(null)} 
        />
      )}
    </div>
  );
};
