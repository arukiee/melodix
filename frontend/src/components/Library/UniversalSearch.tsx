import React, { useState, useEffect, useRef } from 'react';
import { Search, Loader, Clock, X } from 'lucide-react';
import { searchApi, type SearchResult } from '../../api/search';
import { SearchHistoryManager } from '../../services/SearchHistoryManager';
import { SongDetailModal } from './SongDetailModal';

export const UniversalSearch: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedSong, setSelectedSong] = useState<SearchResult | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const debounceTimerRef = useRef<any>(null);

  const executeSearch = async (searchQuery: string) => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }
    setLoading(true);
    setIsOpen(true);
    try {
      const cached = SearchHistoryManager.getCachedResults(searchQuery);
      if (cached) {
        setResults(cached);
      } else {
        const res = await searchApi.searchSongs(searchQuery);
        setResults(res);
        SearchHistoryManager.cacheResults(searchQuery, res);
      }
      SearchHistoryManager.addSearchTerm(searchQuery);
    } catch (err) {
      console.error("Search failed:", err);
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
                  onClick={() => { setQuery(term); setIsOpen(true); }}
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

          {query.trim() && results.length === 0 && !loading && (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>
              No results found for "{query}"
            </div>
          )}

          {results.length > 0 && (
            <div style={{ padding: '8px 0' }}>
              {results.map(res => (
                <div
                  key={res.id}
                  onClick={() => {
                    setSelectedSong(res);
                    setIsOpen(false);
                  }}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    padding: '12px 16px',
                    cursor: 'pointer',
                    borderBottom: '1px solid var(--border-color)',
                  }}
                  className="hover-bg-light"
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: '600' }}>{res.title}</span>
                    <span style={{ fontSize: '0.75rem', padding: '2px 6px', background: 'var(--bg-color)', borderRadius: '10px' }}>
                      {res.provider}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', gap: '8px', marginTop: '4px' }}>
                    <span>{res.artist}</span>
                    <span>•</span>
                    <span style={{ color: res.difficulty.toLowerCase() === 'beginner' ? '#10b981' : 'inherit' }}>
                      {res.difficulty}
                    </span>
                    {(res.hasMidi || res.hasChords) && <span>•</span>}
                    {res.hasMidi && <span style={{ color: '#3b82f6' }}>MIDI</span>}
                    {res.hasChords && <span style={{ color: '#8b5cf6' }}>Chords</span>}
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
