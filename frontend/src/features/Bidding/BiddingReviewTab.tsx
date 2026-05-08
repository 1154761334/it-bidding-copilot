'use client';

import { memo, useMemo } from 'react';

import type { BidProjectDetail } from '@/services/bidding';

interface Props {
  project: BidProjectDetail;
  reviewResult: any;
}

const BiddingReviewTab = memo<Props>(({ project, reviewResult }) => {
  const review = reviewResult || project.review;
  const attachmentByEvidenceId = useMemo<Map<string, any>>(() => {
    const records = review?.attachment_readiness?.records ?? [];
    const indexed = new Map<string, any>();
    for (const item of records) {
      if (item.evidence_id) indexed.set(item.evidence_id, item);
    }
    return indexed;
  }, [review?.attachment_readiness?.records]);

  if (!review) {
    return (
      <div style={{ color: '#999' }}>No review result yet. Run Execute first, then Review.</div>
    );
  }

  return (
    <div>
      <h3 style={{ margin: '0 0 16px' }}>Review Result</h3>

      {review.score_coverage && (
        <div style={{ marginBottom: 16 }}>
          <h4 style={{ margin: '0 0 8px', fontSize: 14 }}>Score Coverage</h4>
          <Badge color="#52c41a">
            {review.score_coverage.covered}/{review.score_coverage.total}
          </Badge>
        </div>
      )}

      {review.hard_clause_coverage && (
        <div style={{ marginBottom: 16 }}>
          <h4 style={{ margin: '0 0 8px', fontSize: 14 }}>Hard Clause Coverage</h4>
          <Badge color="#1677ff">
            {review.hard_clause_coverage.covered}/{review.hard_clause_coverage.total}
          </Badge>
        </div>
      )}

      {review.action_checklist?.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <h4 style={{ margin: '0 0 8px', fontSize: 14 }}>Action Checklist</h4>
          <div style={{ display: 'grid', gap: 8 }}>
            {review.action_checklist.slice(0, 8).map((item: any, index: number) => (
              <div
                key={`${item.area}-${index}`}
                style={{
                  background: '#fafafa',
                  border: '1px solid #e5e5e5',
                  borderRadius: 6,
                  padding: '8px 12px',
                }}
              >
                <div style={{ alignItems: 'center', display: 'flex', gap: 8, marginBottom: 4 }}>
                  <Badge color={item.priority === 'high' ? '#ff4d4f' : '#faad14'}>
                    {item.priority}
                  </Badge>
                  <strong style={{ fontSize: 13 }}>{item.area}</strong>
                  <span style={{ color: '#666', fontSize: 12 }}>owner: {item.owner}</span>
                </div>
                <div style={{ fontSize: 12, lineHeight: 1.5 }}>{item.action}</div>
                {item.references?.length > 0 && (
                  <div style={{ color: '#666', fontSize: 12, marginTop: 3 }}>
                    {item.references.join(', ')}
                  </div>
                )}
                <ActionEvidence attachmentByEvidenceId={attachmentByEvidenceId} item={item} />
              </div>
            ))}
          </div>
        </div>
      )}

      {review.material_groups?.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <h4 style={{ margin: '0 0 8px', fontSize: 14 }}>Material Groups</h4>
          <div style={{ display: 'grid', gap: 8 }}>
            {review.material_groups.map((item: any, index: number) => (
              <div
                key={`${item.key}-${index}`}
                style={{
                  background: '#fafafa',
                  border: '1px solid #e5e5e5',
                  borderRadius: 6,
                  padding: '8px 12px',
                }}
              >
                <div style={{ alignItems: 'center', display: 'flex', gap: 8, marginBottom: 4 }}>
                  <strong style={{ fontSize: 13 }}>{item.label}</strong>
                  <Badge color={item.status === 'covered' ? '#52c41a' : '#faad14'}>
                    {item.status}
                  </Badge>
                  <span style={{ color: '#666', fontSize: 12 }}>owner: {item.owner}</span>
                </div>
                <div style={{ color: '#666', fontSize: 12, lineHeight: 1.5 }}>
                  {item.row_ids?.join(', ')}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {review.commercial_evidence_readiness && (
        <div style={{ marginBottom: 16 }}>
          <h4 style={{ margin: '0 0 8px', fontSize: 14 }}>Commercial Evidence Readiness</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 8 }}>
            <Badge color="#52c41a">
              {review.commercial_evidence_readiness.ready}/
              {review.commercial_evidence_readiness.total} signed
            </Badge>
            <Badge
              color={
                review.commercial_evidence_readiness.needs_page_hint > 0 ? '#faad14' : '#52c41a'
              }
            >
              {review.commercial_evidence_readiness.needs_page_hint} need page or asset
            </Badge>
            <Badge
              color={review.commercial_evidence_readiness.tender_only > 0 ? '#ff4d4f' : '#52c41a'}
            >
              {review.commercial_evidence_readiness.tender_only} tender_only
            </Badge>
          </div>
          {review.commercial_evidence_readiness.not_ready_rows?.length > 0 && (
            <div style={{ display: 'grid', gap: 8 }}>
              {review.commercial_evidence_readiness.not_ready_rows
                .slice(0, 6)
                .map((item: any, index: number) => (
                  <div
                    key={`${item.row_id}-${index}`}
                    style={{
                      background: '#fffbe6',
                      border: '1px solid #ffe58f',
                      borderRadius: 6,
                      fontSize: 12,
                      lineHeight: 1.5,
                      padding: '8px 12px',
                    }}
                  >
                    <div style={{ alignItems: 'center', display: 'flex', gap: 6 }}>
                      <strong>{item.row_id}</strong>
                      <Badge color={item.status === 'tender_only' ? '#ff4d4f' : '#faad14'}>
                        {item.status}
                      </Badge>
                    </div>
                    <div>{item.requirement}</div>
                    <div style={{ color: '#666' }}>
                      bidder: {item.bidder_evidence_ids?.join(', ') || '-'} | tender:{' '}
                      {item.tender_evidence_ids?.join(', ') || '-'}
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>
      )}

      {review.contract_obligation_readiness && (
        <div style={{ marginBottom: 16 }}>
          <h4 style={{ margin: '0 0 8px', fontSize: 14 }}>Contract Obligation Readiness</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 8 }}>
            <Badge color="#52c41a">
              {review.contract_obligation_readiness.ready}/
              {review.contract_obligation_readiness.total} signed
            </Badge>
            <Badge
              color={
                review.contract_obligation_readiness.needs_page_hint > 0 ? '#faad14' : '#52c41a'
              }
            >
              {review.contract_obligation_readiness.needs_page_hint} need page or asset
            </Badge>
            <Badge
              color={review.contract_obligation_readiness.tender_only > 0 ? '#ff4d4f' : '#52c41a'}
            >
              {review.contract_obligation_readiness.tender_only} tender_only
            </Badge>
          </div>
          {review.contract_obligation_readiness.not_ready_rows?.length > 0 && (
            <div style={{ display: 'grid', gap: 8 }}>
              {review.contract_obligation_readiness.not_ready_rows
                .slice(0, 6)
                .map((item: any, index: number) => (
                  <div
                    key={`${item.row_id}-${index}`}
                    style={{
                      background: '#fffbe6',
                      border: '1px solid #ffe58f',
                      borderRadius: 6,
                      fontSize: 12,
                      lineHeight: 1.5,
                      padding: '8px 12px',
                    }}
                  >
                    <div style={{ alignItems: 'center', display: 'flex', gap: 6 }}>
                      <strong>{item.row_id}</strong>
                      <Badge color={item.status === 'tender_only' ? '#ff4d4f' : '#faad14'}>
                        {item.status}
                      </Badge>
                    </div>
                    <div>{item.name || item.requirement}</div>
                    <div style={{ color: '#666' }}>
                      bidder: {item.bidder_evidence_ids?.join(', ') || '-'} | tender:{' '}
                      {item.tender_evidence_ids?.join(', ') || '-'}
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>
      )}

      {review.attachment_readiness && (
        <div style={{ marginBottom: 16 }}>
          <h4 style={{ margin: '0 0 8px', fontSize: 14 }}>Attachment Readiness</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 8 }}>
            <Badge color="#52c41a">
              {review.attachment_readiness.ready}/{review.attachment_readiness.bidder_total} ready
            </Badge>
            <Badge color={review.attachment_readiness.needs_page_hint > 0 ? '#faad14' : '#52c41a'}>
              {review.attachment_readiness.needs_page_hint} need page or asset
            </Badge>
            <Badge color="#1677ff">
              {review.attachment_readiness.tender_references} tender refs
            </Badge>
          </div>
          {review.attachment_readiness.missing_records?.length > 0 && (
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              {review.attachment_readiness.missing_records
                .slice(0, 6)
                .map((item: any, index: number) => (
                  <li
                    key={`${item.evidence_id}-${index}`}
                    style={{ fontSize: 12, marginBottom: 3 }}
                  >
                    {item.evidence_id} {item.title || item.source_doc}
                  </li>
                ))}
            </ul>
          )}
        </div>
      )}

      {review.scoring_readiness && (
        <div style={{ marginBottom: 16 }}>
          <h4 style={{ margin: '0 0 8px', fontSize: 14 }}>Scoring Readiness</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 8 }}>
            <Badge color="#52c41a">
              {review.scoring_readiness.ready}/{review.scoring_readiness.total} ready
            </Badge>
            <Badge color={review.scoring_readiness.needs_page_hint > 0 ? '#faad14' : '#52c41a'}>
              {review.scoring_readiness.needs_page_hint} need page or asset
            </Badge>
            <Badge
              color={review.scoring_readiness.needs_bidder_evidence > 0 ? '#ff4d4f' : '#52c41a'}
            >
              {review.scoring_readiness.needs_bidder_evidence} need bidder evidence
            </Badge>
          </div>
          {review.scoring_readiness.not_ready_rows?.length > 0 && (
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              {review.scoring_readiness.not_ready_rows
                .slice(0, 6)
                .map((item: any, index: number) => (
                  <li key={`${item.row_id}-${index}`} style={{ fontSize: 12, marginBottom: 3 }}>
                    {item.row_id} {item.status}: {item.requirement}
                  </li>
                ))}
            </ul>
          )}
        </div>
      )}

      {review.risk_buckets?.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <h4 style={{ margin: '0 0 8px', fontSize: 14 }}>Risk Buckets</h4>
          <div style={{ display: 'grid', gap: 8 }}>
            {review.risk_buckets.map((bucket: any) => (
              <div
                key={bucket.name}
                style={{
                  background: '#fafafa',
                  border: '1px solid #e5e5e5',
                  borderRadius: 6,
                  padding: '8px 12px',
                }}
              >
                <div style={{ alignItems: 'center', display: 'flex', gap: 8, marginBottom: 6 }}>
                  <strong style={{ fontSize: 13 }}>{bucket.name}</strong>
                  <Badge color={bucket.severity === 'high' ? '#ff4d4f' : '#faad14'}>
                    {bucket.status}
                  </Badge>
                </div>
                <ul style={{ margin: 0, paddingLeft: 18 }}>
                  {bucket.items?.map((item: string, index: number) => (
                    <li key={`${bucket.name}-${index}`} style={{ fontSize: 12, marginBottom: 3 }}>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ marginBottom: 16 }}>
        <h4 style={{ margin: '0 0 8px', fontSize: 14 }}>Findings</h4>
        {review.findings?.length > 0 ? (
          review.findings.map((f: any, i: number) => (
            <div
              key={i}
              style={{
                padding: '8px 12px',
                marginBottom: 8,
                borderRadius: 6,
                background:
                  f.severity === 'high'
                    ? '#fff2f0'
                    : f.severity === 'medium'
                      ? '#fffbe6'
                      : '#f6ffed',
                border: `1px solid ${f.severity === 'high' ? '#ffccc7' : f.severity === 'medium' ? '#ffe58f' : '#b7eb8f'}`,
                fontSize: 13,
              }}
            >
              <strong>[{f.severity}]</strong> {f.area}: {f.message}
              {f.suggestion && (
                <div style={{ marginTop: 4, color: '#666', fontSize: 12 }}>{f.suggestion}</div>
              )}
            </div>
          ))
        ) : (
          <span style={{ color: '#999' }}>No findings</span>
        )}
      </div>
    </div>
  );
});

BiddingReviewTab.displayName = 'BiddingReviewTab';

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

function ActionEvidence({
  attachmentByEvidenceId,
  item,
}: {
  attachmentByEvidenceId: Map<string, any>;
  item: any;
}) {
  const evidenceIds = item.evidence_ids ?? [];
  const rowIds = item.row_ids ?? [];
  const artifactRefs = item.artifact_refs ?? [];

  if (evidenceIds.length === 0 && rowIds.length === 0 && artifactRefs.length === 0) return null;

  return (
    <div aria-label="Action Evidence" style={{ marginTop: 8 }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 6 }}>
        {rowIds.map((rowId: string) => (
          <Badge color="#1677ff" key={rowId}>
            row {rowId}
          </Badge>
        ))}
        {evidenceIds.map((evidenceId: string) => (
          <Badge color="#52c41a" key={evidenceId}>
            {evidenceId}
          </Badge>
        ))}
        {artifactRefs.map((artifact: string) => (
          <Badge color="#722ed1" key={artifact}>
            {artifact}
          </Badge>
        ))}
      </div>
      {evidenceIds.length > 0 && (
        <div style={{ display: 'grid', gap: 4 }}>
          {evidenceIds.slice(0, 6).map((evidenceId: string) => {
            const record = attachmentByEvidenceId.get(evidenceId);
            return (
              <div
                key={`${item.area}-${evidenceId}`}
                style={{
                  borderTop: '1px solid #e5e5e5',
                  color: '#666',
                  fontSize: 12,
                  lineHeight: 1.45,
                  paddingTop: 4,
                }}
              >
                <strong>{evidenceId}</strong>
                {record ? (
                  <span>
                    {' '}
                    {record.status} | rows {record.row_ids?.join(', ') || '-'} |{' '}
                    {record.page_or_asset || record.source_doc}
                  </span>
                ) : (
                  <span> evidence trace not loaded in review payload</span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default BiddingReviewTab;
