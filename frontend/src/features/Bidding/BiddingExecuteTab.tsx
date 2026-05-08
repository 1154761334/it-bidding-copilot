'use client';

import { memo } from 'react';

import type { BidProjectDetail } from '@/services/bidding';

interface Props {
  executeResult: any;
  project: BidProjectDetail;
}

const BiddingExecuteTab = memo<Props>(({ project, executeResult }) => {
  const execution = executeResult || project.execution;

  if (!execution) {
    return (
      <div style={{ color: '#999' }}>No execution result yet. Run Plan first, then Execute.</div>
    );
  }

  return (
    <div>
      <h3 style={{ margin: '0 0 16px' }}>Execute Result</h3>

      <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
        <Stat label="Response Matrix" value={execution.response_matrix_rows ?? '-'} />
        <Stat label="Scoring Table" value={execution.scoring_table_rows ?? '-'} />
        <Stat label="Draft Sections" value={execution.draft_sections ?? '-'} />
      </div>

      {execution.missing_materials?.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <h4 style={{ margin: '0 0 8px', fontSize: 14 }}>Missing Materials</h4>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {execution.missing_materials.map((m: any, i: number) => (
              <li key={i} style={{ fontSize: 13, marginBottom: 4 }}>
                {m.name} - <span style={{ color: '#ff4d4f' }}>{m.status}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
});

BiddingExecuteTab.displayName = 'BiddingExecuteTab';

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div style={{ padding: '8px 16px', background: '#f5f5f5', borderRadius: 6 }}>
      <div style={{ fontSize: 20, fontWeight: 600 }}>{value}</div>
      <div style={{ fontSize: 12, color: '#666' }}>{label}</div>
    </div>
  );
}

export default BiddingExecuteTab;
