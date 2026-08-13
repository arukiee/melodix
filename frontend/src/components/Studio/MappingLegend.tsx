import React from 'react';
import { Keyboard } from 'lucide-react';
import { keyboardMapper } from '../../services/keyboardMapper';

interface MappingLegendProps {
  currentKeyMap: Record<string, number>;
}

export function MappingLegend({ currentKeyMap }: MappingLegendProps) {
  const whiteKeys = ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'"];
  
  return (
    <div style={{
      backgroundColor: 'var(--bg-secondary)',
      border: '1px solid var(--border-color)',
      borderRadius: 'var(--radius-card)',
      padding: '12px 16px',
      display: 'flex',
      flexDirection: 'column',
      gap: '8px'
    }}>
      <h4 style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
        <Keyboard size={14} /> Live Mapping Legend
      </h4>
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        {whiteKeys.map(key => {
          const mappedIndex = currentKeyMap[key];
          if (mappedIndex === undefined) return null;
          
          return (
            <div key={key} style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: '4px',
              padding: '4px 8px',
              minWidth: '36px'
            }}>
              <span style={{ fontSize: '0.9rem', fontWeight: 'bold' }}>{key.toUpperCase()}</span>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>{keyboardMapper.getNoteNameFromIndex(mappedIndex)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
