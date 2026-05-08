'use client';

import { memo, useCallback, useState } from 'react';

import type { EvidenceResult } from '@/services/bidding';

interface Props {
  loading: boolean;
  onSearch: (query: string, category?: string) => Promise<void>;
  results: EvidenceResult[];
}

const CATEGORIES = [
  '',
  'company_info',
  'financial',
  'credit',
  'certificate',
  'project_performance',
  'personnel',
  'product',
  'authorization',
  'service',
  'solution',
  'scoring_rule',
  'requirement',
];

const MATERIAL_GROUP_PRESETS = [
  {
    key: 'qualification_documents',
    label: 'Qualification',
    query: '营业执照 授权 ISO9001 ISO27001 业绩 PMP 软考 资质',
  },
  {
    key: 'commercial_pricing_documents',
    label: 'Commercial',
    query: '开标一览表 投标报价 报价明细 付款 发票 履约保证金',
  },
  {
    key: 'technical_scoring_attachments',
    label: 'Technical',
    query: '技术方案 架构图 功能截图 分布式存储 虚拟化 防火墙 服务编排',
  },
];

const BiddingEvidenceTab = memo<Props>(({ results, loading, onSearch }) => {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');

  const handleSearch = useCallback(() => {
    if (!query.trim()) return;
    onSearch(query.trim(), category || undefined);
  }, [query, category, onSearch]);

  const handlePresetSearch = useCallback(
    (preset: (typeof MATERIAL_GROUP_PRESETS)[number]) => {
      setQuery(preset.query);
      setCategory('');
      onSearch(preset.query);
    },
    [onSearch],
  );

  return (
    <div>
      <h3 style={{ margin: '0 0 16px' }}>Evidence Search</h3>

      {/* Search form */}
      <div style={{ marginBottom: 16, display: 'flex', gap: 8 }}>
        <input
          placeholder="Search evidence..."
          value={query}
          style={{
            flex: 1,
            padding: '8px 12px',
            border: '1px solid #d9d9d9',
            borderRadius: 6,
            fontSize: 13,
          }}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
        <select
          value={category}
          style={{
            padding: '8px 12px',
            border: '1px solid #d9d9d9',
            borderRadius: 6,
            fontSize: 13,
          }}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="">All categories</option>
          {CATEGORIES.filter(Boolean).map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <button
          disabled={loading || !query.trim()}
          style={{
            padding: '8px 16px',
            background: '#1677ff',
            color: '#fff',
            border: 'none',
            borderRadius: 6,
            cursor: loading ? 'wait' : 'pointer',
            fontSize: 13,
          }}
          onClick={handleSearch}
        >
          {loading ? '...' : 'Search'}
        </button>
      </div>

      <div style={{ marginBottom: 16 }}>
        <h4 style={{ margin: '0 0 8px', fontSize: 14 }}>Material Group Presets</h4>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {MATERIAL_GROUP_PRESETS.map((preset) => (
            <button
              disabled={loading}
              key={preset.key}
              type="button"
              style={{
                background: '#fafafa',
                border: '1px solid #d9d9d9',
                borderRadius: 4,
                color: '#333',
                cursor: loading ? 'wait' : 'pointer',
                fontSize: 12,
                padding: '5px 9px',
              }}
              onClick={() => handlePresetSearch(preset)}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div>
          <h4 style={{ margin: '0 0 8px', fontSize: 14 }}>{results.length} results</h4>
          {results.map((r) => (
            <div
              key={r.evidence_id}
              style={{
                padding: 12,
                marginBottom: 8,
                background: '#fafafa',
                border: '1px solid #e5e5e5',
                borderRadius: 6,
                fontSize: 13,
              }}
            >
              <div style={{ fontWeight: 500, marginBottom: 4 }}>
                [{r.evidence_id}] {r.title}
              </div>
              <div style={{ color: '#666', marginBottom: 4 }}>
                Category: {r.category} | Source: {r.source_doc} | Status: {r.verified_status}
              </div>
              {r.summary && (
                <div style={{ color: '#333', fontSize: 12 }}>{r.summary.slice(0, 200)}...</div>
              )}
              {r.asset_paths?.length > 0 && (
                <div style={{ color: '#999', fontSize: 11, marginTop: 4 }}>
                  {r.asset_paths.length} assets
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {!loading && results.length === 0 && query && (
        <div style={{ color: '#999' }}>No results found</div>
      )}
    </div>
  );
});

BiddingEvidenceTab.displayName = 'BiddingEvidenceTab';
export default BiddingEvidenceTab;
