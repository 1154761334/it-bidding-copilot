'use client';

import { memo, useCallback, useRef } from 'react';

import type { BidProjectDetail } from '@/services/bidding';

interface Props {
  loading: boolean;
  onUpload: (projectId: string, file: File, purpose: string) => Promise<void>;
  project: BidProjectDetail;
}

const BiddingFilesTab = memo<Props>(({ project, onUpload, loading }) => {
  const fileRef = useRef<HTMLInputElement>(null);

  const handleUpload = useCallback(
    async (purpose: string) => {
      const file = fileRef.current?.files?.[0];
      if (!file) return;
      await onUpload(project.id, file, purpose);
      if (fileRef.current) fileRef.current.value = '';
    },
    [project.id, onUpload],
  );

  return (
    <div>
      <h3 style={{ margin: '0 0 16px' }}>File Sources</h3>

      {/* Upload */}
      <div style={{ marginBottom: 24, padding: 16, background: '#f5f5f5', borderRadius: 8 }}>
        <input accept=".docx,.pdf,.md,.txt" ref={fileRef} style={{ marginBottom: 8 }} type="file" />
        <div style={{ display: 'flex', gap: 8 }}>
          {['tender', 'historical_bid', 'company_credential', 'vendor_material'].map((purpose) => (
            <button
              disabled={loading}
              key={purpose}
              style={{
                padding: '6px 12px',
                background: '#1677ff',
                color: '#fff',
                border: 'none',
                borderRadius: 4,
                cursor: loading ? 'wait' : 'pointer',
                fontSize: 12,
              }}
              onClick={() => handleUpload(purpose)}
            >
              Upload as {purpose.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* File list */}
      <div>
        <h4 style={{ margin: '0 0 8px' }}>Uploaded Files</h4>
        {project.source_files?.length > 0 ? (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #e5e5e5' }}>
                <th style={{ textAlign: 'left', padding: 8 }}>Filename</th>
                <th style={{ textAlign: 'left', padding: 8 }}>Purpose</th>
                <th style={{ textAlign: 'left', padding: 8 }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {project.source_files.map((f: any, i: number) => (
                <tr key={i} style={{ borderBottom: '1px solid #f0f0f0' }}>
                  <td style={{ padding: 8 }}>{f.filename}</td>
                  <td style={{ padding: 8 }}>{f.source_type}</td>
                  <td style={{ padding: 8 }}>{f.parse_status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{ color: '#999', fontSize: 13 }}>No files uploaded yet</div>
        )}
      </div>
    </div>
  );
});

BiddingFilesTab.displayName = 'BiddingFilesTab';
export default BiddingFilesTab;
