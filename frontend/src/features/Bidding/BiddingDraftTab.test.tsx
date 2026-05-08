import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { ArtifactInfo, EvidenceTraceRecord, MaterialGroup } from '@/services/bidding';

import BiddingDraftTab from './BiddingDraftTab';

const CONTRACT_BINDING_HINT = '服务期、验收、违约责任、转让分包和合同签署承诺需与投标响应一致。';

const artifacts: ArtifactInfo[] = [
  {
    modified: '2026-05-08T09:30:00Z',
    name: 'draft.md',
    size: 2048,
  },
];

const materialGroups: MaterialGroup[] = [
  {
    binding_hint: CONTRACT_BINDING_HINT,
    evidence_ids: ['EVID-131'],
    key: 'contract_execution_documents',
    label: '合同履约材料',
    missing_rows: ['C2'],
    owner: 'legal',
    row_ids: ['C1', 'C2'],
    status: 'needs_signoff',
  },
];

const currentEvidenceTrace: EvidenceTraceRecord[] = [
  {
    asset_paths: ['vault/contracts/service-commitment.md'],
    evidence_id: 'EVID-131',
    heading_path: '合同条款 / 售后服务',
    material_group: '合同履约材料',
    material_group_key: 'contract_execution_documents',
    material_owner: 'legal',
    page_hint: 'p.23',
    row_id: 'C1',
    source_doc: '招标文件.md',
    title: '9.3.4.1售后服务承诺',
  },
];

const currentArtifact = [
  '# 投标文件',
  '## 七、证据索引',
  '| 材料包 | 行号 | 证据 |',
  '| --- | --- | --- |',
  '| 合同履约材料 | C1 | EVID-131 |',
].join('\n');

describe('BiddingDraftTab', () => {
  it('renders artifact material package jumps and opens the matching trace record', () => {
    render(
      <BiddingDraftTab
        artifacts={artifacts}
        currentArtifact={currentArtifact}
        currentArtifactName="draft.md"
        currentEvidenceTrace={currentEvidenceTrace}
        loading={false}
        materialGroups={materialGroups}
        projectId="project-1"
        onFetchArtifact={vi.fn().mockResolvedValue(undefined)}
      />,
    );

    expect(screen.getByText('Artifact Material Packages')).toBeInTheDocument();

    const contractPackage = screen.getByTitle(CONTRACT_BINDING_HINT);
    expect(within(contractPackage).getByText('合同履约材料')).toBeInTheDocument();
    expect(within(contractPackage).getByText('Rows 1')).toBeInTheDocument();
    expect(within(contractPackage).getByText('Evidence 1')).toBeInTheDocument();
    expect(within(contractPackage).getByText('Trace 1')).toBeInTheDocument();
    expect(within(contractPackage).getByText('Missing 1')).toBeInTheDocument();

    fireEvent.click(contractPackage);

    expect(screen.getByText('Selected Evidence')).toBeInTheDocument();
    expect(screen.getAllByText('EVID-131').length).toBeGreaterThan(0);
    expect(screen.getAllByText('9.3.4.1售后服务承诺').length).toBeGreaterThan(0);
    expect(screen.getAllByText('合同履约材料').length).toBeGreaterThan(1);
  });
});
