'use client';

import { memo } from 'react';

import type { BidProjectDetail } from '@/services/bidding';

interface Props {
  planResult: any;
  project: BidProjectDetail;
}

const BiddingPlanTab = memo<Props>(({ project, planResult }) => {
  const plan = planResult?.plan || project.plan;

  if (!plan) {
    return (
      <div style={{ color: '#999' }}>No plan generated yet. Click "Analyze / Plan" to begin.</div>
    );
  }

  return (
    <div>
      <h3 style={{ margin: '0 0 16px' }}>Plan Result</h3>

      <Section title="Project Info">
        <pre
          style={{
            fontSize: 12,
            background: '#f5f5f5',
            padding: 12,
            borderRadius: 6,
            overflow: 'auto',
          }}
        >
          {JSON.stringify(plan.project_info || {}, null, 2)}
        </pre>
      </Section>

      <Section title={`Requirements (${plan.requirements_count || 0})`}>
        <Badge color="#1677ff">{plan.requirements_count || 0} items</Badge>
      </Section>

      <Section title={`Scoring Items (${plan.scoring_items_count || 0})`}>
        <Badge color="#52c41a">{plan.scoring_items_count || 0} items</Badge>
      </Section>

      <Section title={`Hard Clauses (${plan.hard_clauses_count || 0})`}>
        <Badge color="#ff4d4f">{plan.hard_clauses_count || 0} items</Badge>
      </Section>

      <Section title="Missing Materials">
        {plan.missing_materials?.length > 0 ? (
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {plan.missing_materials.map((m: any, i: number) => (
              <li key={i} style={{ fontSize: 13, marginBottom: 4 }}>
                {m.name} - <span style={{ color: '#ff4d4f' }}>{m.status}</span>
              </li>
            ))}
          </ul>
        ) : (
          <span style={{ color: '#999' }}>None</span>
        )}
      </Section>

      <Section title="Evidence Items">
        {plan.evidence_items?.length > 0 ? (
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {plan.evidence_items.map((e: any, i: number) => (
              <li key={i} style={{ fontSize: 13, marginBottom: 4 }}>
                {e.name} -{' '}
                <span style={{ color: e.status === 'missing' ? '#ff4d4f' : '#52c41a' }}>
                  {e.status}
                </span>
                {e.evidence_ids?.length > 0 && (
                  <span style={{ color: '#999', marginLeft: 8 }}>
                    ({e.evidence_ids.join(', ')})
                  </span>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <span style={{ color: '#999' }}>None</span>
        )}
      </Section>
    </div>
  );
});

BiddingPlanTab.displayName = 'BiddingPlanTab';

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <h4 style={{ margin: '0 0 8px', fontSize: 14 }}>{title}</h4>
      {children}
    </div>
  );
}

function Badge({ children, color }: { children: React.ReactNode; color: string }) {
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '2px 8px',
        background: color + '20',
        color,
        borderRadius: 4,
        fontSize: 12,
        fontWeight: 500,
      }}
    >
      {children}
    </span>
  );
}

export default BiddingPlanTab;
