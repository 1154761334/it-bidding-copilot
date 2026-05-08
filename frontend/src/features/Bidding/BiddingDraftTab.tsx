'use client';

import { PackageCheck } from 'lucide-react';
import {
  type CSSProperties,
  memo,
  type ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react';

import type { ArtifactInfo, EvidenceTraceRecord, MaterialGroup } from '@/services/bidding';

const CONTRACT_EXECUTION_GROUP_KEY = 'contract_execution_documents';

interface Props {
  artifacts: ArtifactInfo[];
  currentArtifact: string | null;
  currentArtifactName: string | null;
  currentEvidenceTrace: EvidenceTraceRecord[];
  loading: boolean;
  materialGroups?: MaterialGroup[];
  onFetchArtifact: (projectId: string, name: string) => Promise<void>;
  projectId: string;
}

const BiddingDraftTab = memo<Props>(
  ({
    projectId,
    artifacts,
    currentArtifact,
    currentArtifactName,
    currentEvidenceTrace,
    loading,
    materialGroups,
    onFetchArtifact,
  }) => {
    const handleFetch = useCallback(
      (name: string) => {
        onFetchArtifact(projectId, name);
      },
      [projectId, onFetchArtifact],
    );

    useEffect(() => {
      if (loading || currentArtifact || currentArtifactName || artifacts.length === 0) return;

      const defaultArtifact =
        artifacts.find((artifact) => artifact.name === 'draft.md') ?? artifacts[0];
      handleFetch(defaultArtifact.name);
    }, [artifacts, currentArtifact, currentArtifactName, handleFetch, loading]);

    const selectedArtifact = useMemo(
      () => artifacts.find((artifact) => artifact.name === currentArtifactName) ?? null,
      [artifacts, currentArtifactName],
    );
    const evidenceCount = useMemo(
      () => new Set(currentArtifact?.match(/EVID-\d+/g) ?? []).size,
      [currentArtifact],
    );

    return (
      <div>
        <h3 style={{ margin: '0 0 16px' }}>Draft & Artifacts</h3>

        {/* Artifact list */}
        <div style={{ marginBottom: 16 }}>
          <h4 style={{ margin: '0 0 8px', fontSize: 14 }}>Available Artifacts</h4>
          {artifacts.length > 0 ? (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {artifacts.map((a) => (
                <button
                  disabled={loading}
                  key={a.name}
                  style={{
                    padding: '4px 10px',
                    background: currentArtifactName === a.name ? '#e6f4ff' : '#f5f5f5',
                    border:
                      currentArtifactName === a.name ? '1px solid #91caff' : '1px solid #d9d9d9',
                    borderRadius: 4,
                    cursor: 'pointer',
                    color: currentArtifactName === a.name ? '#1677ff' : '#333',
                    fontSize: 12,
                  }}
                  onClick={() => handleFetch(a.name)}
                >
                  {a.name}
                  <span style={{ color: '#999', marginLeft: 6 }}>{formatBytes(a.size)}</span>
                </button>
              ))}
            </div>
          ) : (
            <span style={{ color: '#999' }}>No artifacts generated yet</span>
          )}
        </div>

        {/* Artifact content */}
        {loading && <div style={{ color: '#999' }}>Loading...</div>}
        {currentArtifact && (
          <div>
            <div
              style={{
                alignItems: 'center',
                display: 'flex',
                gap: 8,
                justifyContent: 'space-between',
                marginBottom: 8,
              }}
            >
              <h4 style={{ margin: 0, fontSize: 14 }}>
                {selectedArtifact?.name ?? currentArtifactName ?? 'Content'}
              </h4>
              <div style={{ color: '#666', display: 'flex', gap: 8, fontSize: 12 }}>
                {selectedArtifact && <span>{formatBytes(selectedArtifact.size)}</span>}
                {selectedArtifact && <span>{formatModified(selectedArtifact.modified)}</span>}
                {evidenceCount > 0 && <span>{evidenceCount} evidence ids</span>}
              </div>
            </div>
            <ArtifactPreview
              content={currentArtifact}
              evidenceTrace={currentEvidenceTrace}
              materialGroups={materialGroups}
              name={currentArtifactName}
            />
          </div>
        )}
      </div>
    );
  },
);

BiddingDraftTab.displayName = 'BiddingDraftTab';
export default BiddingDraftTab;

function formatBytes(size: number) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

function formatModified(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

type EvidenceTraceMap = Map<string, EvidenceTraceRecord[]>;

interface InlineRenderOptions {
  onSelectEvidence?: (evidenceId: string) => void;
  selectedEvidenceId?: string | null;
  traceById?: EvidenceTraceMap;
}

function ArtifactPreview({
  content,
  evidenceTrace,
  materialGroups,
  name,
}: {
  content: string;
  evidenceTrace: EvidenceTraceRecord[];
  materialGroups?: MaterialGroup[];
  name: string | null;
}) {
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null);
  const [selectedMaterialGroupKey, setSelectedMaterialGroupKey] = useState('all');
  const traceById = useMemo(() => groupEvidenceTrace(evidenceTrace), [evidenceTrace]);
  const materialGroupOptions = useMemo(
    () => normalizeMaterialGroups(materialGroups),
    [materialGroups],
  );
  const selectedMaterialGroup = useMemo(
    () => materialGroupOptions.find((item) => item.key === selectedMaterialGroupKey) ?? null,
    [materialGroupOptions, selectedMaterialGroupKey],
  );
  const artifactEvidenceIds = useMemo(() => new Set(content.match(/EVID-\d+/g) ?? []), [content]);
  const filteredTraceRecords = useMemo(
    () => filterEvidenceTrace(evidenceTrace, artifactEvidenceIds, selectedMaterialGroup),
    [artifactEvidenceIds, evidenceTrace, selectedMaterialGroup],
  );
  const artifactMaterialPackages = useMemo(
    () =>
      buildArtifactMaterialPackages(
        materialGroupOptions,
        evidenceTrace,
        artifactEvidenceIds,
        content,
      ),
    [artifactEvidenceIds, content, evidenceTrace, materialGroupOptions],
  );
  const selectedTrace = selectedEvidenceId ? traceById.get(selectedEvidenceId) : null;

  useEffect(() => {
    if (!selectedEvidenceId) return;
    if (filteredTraceRecords.some((record) => record.evidence_id === selectedEvidenceId)) return;
    setSelectedEvidenceId(null);
  }, [filteredTraceRecords, selectedEvidenceId]);

  const handleSelectMaterialPackage = useCallback(
    (key: string) => {
      const materialGroup = materialGroupOptions.find((item) => item.key === key) ?? null;
      const nextRecords = filterEvidenceTrace(evidenceTrace, artifactEvidenceIds, materialGroup);

      setSelectedMaterialGroupKey(key);
      if (nextRecords[0]) setSelectedEvidenceId(nextRecords[0].evidence_id);
    },
    [artifactEvidenceIds, evidenceTrace, materialGroupOptions],
  );

  if (name?.endsWith('.json')) return <RawArtifact content={content} />;

  const inlineOptions: InlineRenderOptions = {
    onSelectEvidence: setSelectedEvidenceId,
    selectedEvidenceId,
    traceById,
  };

  return (
    <div>
      {artifactMaterialPackages.length > 0 && (
        <ArtifactMaterialPackageSummary
          materialPackages={artifactMaterialPackages}
          selectedMaterialGroupKey={selectedMaterialGroupKey}
          onSelectMaterialPackage={handleSelectMaterialPackage}
        />
      )}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
        <div
          style={{
            background: '#fff',
            border: '1px solid #e5e5e5',
            borderRadius: 6,
            flex: '1 1 auto',
            fontSize: 13,
            lineHeight: 1.65,
            maxHeight: 560,
            minWidth: 0,
            overflow: 'auto',
            padding: 12,
          }}
        >
          {renderMarkdownBlocks(content, inlineOptions)}
        </div>
        {evidenceTrace.length > 0 && (
          <EvidenceTracePanel
            evidenceId={selectedEvidenceId}
            filteredRecords={filteredTraceRecords}
            materialGroups={materialGroupOptions}
            records={selectedTrace ?? []}
            selectedMaterialGroupKey={selectedMaterialGroupKey}
            onSelectEvidence={setSelectedEvidenceId}
            onSelectMaterialGroup={setSelectedMaterialGroupKey}
          />
        )}
      </div>
    </div>
  );
}

function RawArtifact({ content }: { content: string }) {
  return (
    <pre
      style={{
        background: '#f5f5f5',
        borderRadius: 6,
        fontSize: 12,
        maxHeight: 560,
        overflow: 'auto',
        padding: 12,
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
      }}
    >
      {content}
    </pre>
  );
}

function renderMarkdownBlocks(content: string, inlineOptions: InlineRenderOptions = {}) {
  const lines = content.split(/\r?\n/);
  const blocks: ReactNode[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    if (!trimmed) continue;

    const headingLevel = getHeadingLevel(trimmed);
    if (headingLevel > 0) {
      const headingText = trimmed.slice(headingLevel).trim();
      blocks.push(
        <div
          key={`heading-${i}`}
          style={{
            fontSize: headingLevel === 1 ? 20 : headingLevel === 2 ? 17 : 14,
            fontWeight: 700,
            margin: headingLevel === 1 ? '0 0 14px' : '14px 0 8px',
          }}
        >
          {renderInlineText(headingText, inlineOptions)}
        </div>,
      );
      continue;
    }

    if (isTableRow(trimmed) && isTableSeparator(lines[i + 1]?.trim() ?? '')) {
      const header = splitMarkdownRow(trimmed);
      const rows: string[][] = [];
      i += 2;
      while (i < lines.length && isTableRow(lines[i].trim())) {
        rows.push(splitMarkdownRow(lines[i].trim()));
        i++;
      }
      i--;
      blocks.push(
        <MarkdownTable
          header={header}
          inlineOptions={inlineOptions}
          key={`table-${i}`}
          rows={rows}
        />,
      );
      continue;
    }

    if (trimmed.startsWith('- ')) {
      const items: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith('- ')) {
        items.push(lines[i].trim().slice(2));
        i++;
      }
      i--;
      blocks.push(
        <ul key={`list-${i}`} style={{ margin: '6px 0 10px', paddingLeft: 20 }}>
          {items.map((item, index) => (
            <li key={`${index}-${item.slice(0, 16)}`} style={{ marginBottom: 4 }}>
              {renderInlineText(item, inlineOptions)}
            </li>
          ))}
        </ul>,
      );
      continue;
    }

    blocks.push(
      <p key={`p-${i}`} style={{ margin: '6px 0' }}>
        {renderInlineText(trimmed, inlineOptions)}
      </p>,
    );
  }

  return blocks.length > 0 ? blocks : <RawArtifact content={content} />;
}

function MarkdownTable({
  header,
  inlineOptions,
  rows,
}: {
  header: string[];
  inlineOptions: InlineRenderOptions;
  rows: string[][];
}) {
  return (
    <div style={{ margin: '8px 0 14px', overflowX: 'auto' }}>
      <table
        style={{
          borderCollapse: 'collapse',
          minWidth: '100%',
          tableLayout: 'fixed',
        }}
      >
        <thead>
          <tr>
            {header.map((cell, index) => (
              <th
                key={`${index}-${cell}`}
                style={{
                  background: '#fafafa',
                  border: '1px solid #e5e5e5',
                  fontSize: 12,
                  fontWeight: 600,
                  padding: '6px 8px',
                  textAlign: 'left',
                  verticalAlign: 'top',
                }}
              >
                {renderInlineText(cell, inlineOptions)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {header.map((_, cellIndex) => (
                <td
                  key={cellIndex}
                  style={{
                    border: '1px solid #e5e5e5',
                    padding: '6px 8px',
                    verticalAlign: 'top',
                    wordBreak: 'break-word',
                  }}
                >
                  {renderInlineText(row[cellIndex] ?? '', inlineOptions)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function renderInlineText(text: string, options: InlineRenderOptions = {}) {
  const parts = text.replaceAll('\\|', '|').split(/(EVID-\d+)/g);
  return parts.map((part, index) =>
    /^EVID-\d+$/.test(part) ? (
      renderEvidenceBadge(part, index, options)
    ) : (
      <span key={`${index}-${part.slice(0, 12)}`}>{part}</span>
    ),
  );
}

function renderEvidenceBadge(evidenceId: string, index: number, options: InlineRenderOptions) {
  const records = options.traceById?.get(evidenceId) ?? [];
  const traced = records.length > 0;
  const selected = options.selectedEvidenceId === evidenceId;

  if (!traced || !options.onSelectEvidence) {
    return (
      <span
        key={`${evidenceId}-${index}`}
        style={evidenceBadgeStyle({ selected: false, traced })}
        title="No evidence trace loaded"
      >
        {evidenceId}
      </span>
    );
  }

  return (
    <button
      key={`${evidenceId}-${index}`}
      style={evidenceBadgeStyle({ selected, traced })}
      title={traceTitle(records)}
      type="button"
      onClick={() => options.onSelectEvidence?.(evidenceId)}
    >
      {evidenceId}
    </button>
  );
}

function evidenceBadgeStyle({ selected, traced }: { selected: boolean; traced: boolean }) {
  return {
    background: selected ? '#e6f4ff' : traced ? '#f6ffed' : '#f5f5f5',
    border: `1px solid ${selected ? '#91caff' : traced ? '#b7eb8f' : '#d9d9d9'}`,
    borderRadius: 3,
    color: selected ? '#1677ff' : traced ? '#389e0d' : '#666',
    cursor: traced ? 'pointer' : 'default',
    display: 'inline-block',
    fontFamily: 'monospace',
    fontSize: 12,
    lineHeight: 1.45,
    margin: '0 2px',
    padding: '0 3px',
  } satisfies CSSProperties;
}

function EvidenceTracePanel({
  evidenceId,
  filteredRecords,
  materialGroups,
  records,
  selectedMaterialGroupKey,
  onSelectEvidence,
  onSelectMaterialGroup,
}: {
  evidenceId: string | null;
  filteredRecords: EvidenceTraceRecord[];
  materialGroups: MaterialGroup[];
  records: EvidenceTraceRecord[];
  selectedMaterialGroupKey: string;
  onSelectEvidence: (evidenceId: string) => void;
  onSelectMaterialGroup: (key: string) => void;
}) {
  const summaries = useMemo(() => summarizeTraceRecords(filteredRecords), [filteredRecords]);

  return (
    <aside
      style={{
        background: '#fafafa',
        border: '1px solid #e5e5e5',
        borderRadius: 6,
        flex: '0 0 280px',
        fontSize: 12,
        maxHeight: 560,
        overflow: 'auto',
        padding: 12,
      }}
    >
      <div style={{ color: '#666', marginBottom: 4 }}>Evidence Trace</div>
      {materialGroups.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ color: '#999', marginBottom: 6 }}>Material Group Filter</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            <TraceFilterButton
              active={selectedMaterialGroupKey === 'all'}
              label="All"
              onClick={() => onSelectMaterialGroup('all')}
            />
            {materialGroups.map((item) => (
              <TraceFilterButton
                active={selectedMaterialGroupKey === item.key}
                key={item.key}
                label={`${item.label} ${item.evidence_ids.length}`}
                onClick={() => onSelectMaterialGroup(item.key)}
              />
            ))}
          </div>
        </div>
      )}
      {evidenceId && records.length > 0 && (
        <div style={{ marginBottom: 14 }}>
          <div style={{ color: '#999', marginBottom: 4 }}>Selected Evidence</div>
          <div style={{ fontFamily: 'monospace', fontSize: 13, fontWeight: 700, marginBottom: 8 }}>
            {evidenceId}
          </div>
          {records.map((record, index) => (
            <div
              key={`${record.row_id}-${index}`}
              style={{
                borderTop: index === 0 ? 'none' : '1px solid #e5e5e5',
                paddingTop: index === 0 ? 0 : 10,
                marginTop: index === 0 ? 0 : 10,
              }}
            >
              <TraceField label="Material group" value={record.material_group || 'Unclassified'} />
              <TraceField label="Row" value={record.row_id} />
              <TraceField label="Title" value={cleanTraceText(record.title)} />
              <TraceField label="Source" value={record.source_doc} />
              <TraceField label="Location" value={cleanTraceText(record.heading_path)} />
              <TraceField label="Page / Asset hint" value={record.page_hint || 'Not provided'} />
              {record.asset_paths && record.asset_paths.length > 0 && (
                <TraceField label="Asset paths" value={record.asset_paths.join(', ')} />
              )}
            </div>
          ))}
        </div>
      )}
      <div style={{ color: '#999', marginBottom: 6 }}>Trace Records</div>
      {summaries.length > 0 ? (
        <div style={{ display: 'grid', gap: 6 }}>
          {summaries.slice(0, 24).map((item) => (
            <button
              key={item.evidence_id}
              type="button"
              style={{
                background: evidenceId === item.evidence_id ? '#e6f4ff' : '#fff',
                border: evidenceId === item.evidence_id ? '1px solid #91caff' : '1px solid #e5e5e5',
                borderRadius: 4,
                color: '#333',
                cursor: 'pointer',
                fontSize: 12,
                padding: '6px 8px',
                textAlign: 'left',
              }}
              onClick={() => onSelectEvidence(item.evidence_id)}
            >
              <div style={{ fontFamily: 'monospace', fontWeight: 700 }}>
                {item.evidence_id}
                <span style={{ color: '#999', fontFamily: 'system-ui, sans-serif', marginLeft: 6 }}>
                  {item.material_group}
                </span>
              </div>
              <div style={{ color: '#666', lineHeight: 1.45 }}>{cleanTraceText(item.title)}</div>
              <div style={{ color: '#999', lineHeight: 1.45 }}>
                rows {item.row_ids.join(', ')} | {item.source_doc}
              </div>
            </button>
          ))}
        </div>
      ) : (
        <div style={{ color: '#999' }}>No trace records for this material group</div>
      )}
    </aside>
  );
}

function TraceFilterButton({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      style={{
        background: active ? '#e6f4ff' : '#fff',
        border: `1px solid ${active ? '#91caff' : '#e5e5e5'}`,
        borderRadius: 4,
        color: active ? '#1677ff' : '#333',
        cursor: 'pointer',
        fontSize: 12,
        padding: '3px 7px',
      }}
      onClick={onClick}
    >
      {label}
    </button>
  );
}

function ArtifactMaterialPackageSummary({
  materialPackages,
  selectedMaterialGroupKey,
  onSelectMaterialPackage,
}: {
  materialPackages: Array<MaterialGroup & { trace_count: number; visible_evidence_ids: string[] }>;
  selectedMaterialGroupKey: string;
  onSelectMaterialPackage: (key: string) => void;
}) {
  return (
    <section style={{ marginBottom: 10 }}>
      <div
        style={{
          alignItems: 'center',
          color: '#666',
          display: 'flex',
          fontSize: 12,
          gap: 6,
          marginBottom: 6,
        }}
      >
        <PackageCheck size={14} />
        <span>Artifact Material Packages</span>
      </div>
      <div
        style={{
          display: 'grid',
          gap: 6,
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        }}
      >
        {materialPackages.map((item) => {
          const active = selectedMaterialGroupKey === item.key;
          const emphasized = item.key === CONTRACT_EXECUTION_GROUP_KEY;

          return (
            <button
              key={item.key}
              title={item.binding_hint}
              type="button"
              style={{
                background: active ? '#e6f4ff' : '#fff',
                border: `1px solid ${active ? '#91caff' : emphasized ? '#ffd591' : '#e5e5e5'}`,
                borderRadius: 6,
                color: '#333',
                cursor: 'pointer',
                padding: '8px 10px',
                textAlign: 'left',
              }}
              onClick={() => onSelectMaterialPackage(item.key)}
            >
              <div
                style={{
                  alignItems: 'center',
                  display: 'flex',
                  gap: 6,
                  justifyContent: 'space-between',
                  marginBottom: 6,
                }}
              >
                <span style={{ fontSize: 13, fontWeight: 700 }}>{item.label}</span>
                <span style={{ color: active ? '#1677ff' : '#999', fontSize: 11 }}>Open trace</span>
              </div>
              <div
                style={{ color: '#666', display: 'flex', flexWrap: 'wrap', gap: 8, fontSize: 11 }}
              >
                <span>Rows {item.row_ids.length}</span>
                <span>Evidence {item.visible_evidence_ids.length}</span>
                <span>Trace {item.trace_count}</span>
                {item.missing_rows.length > 0 && <span>Missing {item.missing_rows.length}</span>}
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function TraceField({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ color: '#999', marginBottom: 2 }}>{label}</div>
      <div style={{ color: '#333', wordBreak: 'break-word' }}>{value}</div>
    </div>
  );
}

function normalizeMaterialGroups(groups?: MaterialGroup[]) {
  return (groups ?? [])
    .filter((item) => item?.key && item?.label)
    .map((item) => ({
      ...item,
      evidence_ids: Array.isArray(item.evidence_ids) ? item.evidence_ids : [],
      row_ids: Array.isArray(item.row_ids) ? item.row_ids : [],
    }));
}

function filterEvidenceTrace(
  records: EvidenceTraceRecord[],
  artifactEvidenceIds: Set<string>,
  materialGroup: MaterialGroup | null,
) {
  return records.filter((record) => {
    const inArtifact =
      artifactEvidenceIds.size === 0 || artifactEvidenceIds.has(record.evidence_id);
    if (!inArtifact) return false;
    if (!materialGroup) return true;

    return (
      record.material_group_key === materialGroup.key ||
      record.material_group === materialGroup.label ||
      materialGroup.evidence_ids.includes(record.evidence_id) ||
      materialGroup.row_ids.includes(record.row_id)
    );
  });
}

function buildArtifactMaterialPackages(
  materialGroups: MaterialGroup[],
  records: EvidenceTraceRecord[],
  artifactEvidenceIds: Set<string>,
  content: string,
) {
  return materialGroups
    .map((group) => {
      const traceRecords = filterEvidenceTrace(records, artifactEvidenceIds, group);
      const visibleEvidenceIds = [
        ...new Set([
          ...traceRecords.map((record) => record.evidence_id).filter(Boolean),
          ...group.evidence_ids.filter((evidenceId) => artifactEvidenceIds.has(evidenceId)),
        ]),
      ];
      const visibleRowIds = [
        ...new Set([
          ...traceRecords.map((record) => record.row_id).filter(Boolean),
          ...group.row_ids.filter((rowId) => content.includes(rowId)),
        ]),
      ];

      return {
        ...group,
        row_ids: visibleRowIds,
        trace_count: traceRecords.length,
        visible_evidence_ids: visibleEvidenceIds,
      };
    })
    .filter(
      (group) =>
        group.visible_evidence_ids.length > 0 ||
        group.row_ids.length > 0 ||
        group.key === CONTRACT_EXECUTION_GROUP_KEY,
    );
}

function summarizeTraceRecords(records: EvidenceTraceRecord[]) {
  const grouped = new Map<
    string,
    {
      evidence_id: string;
      material_group: string;
      row_ids: string[];
      source_doc: string;
      title: string;
    }
  >();

  for (const record of records) {
    if (!record.evidence_id) continue;
    const existing = grouped.get(record.evidence_id);
    if (existing) {
      existing.row_ids = appendUnique(existing.row_ids, record.row_id);
      continue;
    }
    grouped.set(record.evidence_id, {
      evidence_id: record.evidence_id,
      material_group: record.material_group || 'Unclassified',
      row_ids: record.row_id ? [record.row_id] : [],
      source_doc: record.source_doc,
      title: record.title,
    });
  }

  return [...grouped.values()].sort((left, right) =>
    left.evidence_id.localeCompare(right.evidence_id, undefined, { numeric: true }),
  );
}

function appendUnique(values: string[], value: string) {
  if (!value || values.includes(value)) return values;
  return [...values, value];
}

function groupEvidenceTrace(records: EvidenceTraceRecord[]) {
  const grouped: EvidenceTraceMap = new Map();
  for (const record of records) {
    if (!record.evidence_id) continue;
    const existing = grouped.get(record.evidence_id) ?? [];
    existing.push(record);
    grouped.set(record.evidence_id, existing);
  }
  return grouped;
}

function traceTitle(records: EvidenceTraceRecord[]) {
  const first = records[0];
  if (!first) return 'Evidence trace unavailable';

  return `${first.evidence_id} | ${cleanTraceText(first.title)} | ${first.source_doc}`;
}

function cleanTraceText(value: string) {
  return value.replaceAll(/<[^>]+>/g, '');
}

function isTableRow(line: string) {
  return line.startsWith('|') && line.endsWith('|');
}

function isTableSeparator(line: string) {
  const normalized = line.replace(/^\|/, '').replace(/\|$/, '');
  const cells = normalized.split('|');

  return (
    cells.length > 1 &&
    cells.every((cell) => {
      const trimmed = cell.trim();
      const withoutAlignment = trimmed.replace(/^:/, '').replace(/:$/, '');
      return withoutAlignment.length >= 3 && [...withoutAlignment].every((char) => char === '-');
    })
  );
}

function splitMarkdownRow(line: string) {
  const normalized = line.replace(/^\|/, '').replace(/\|$/, '');
  const cells: string[] = [];
  let current = '';
  let escaped = false;

  for (const char of normalized) {
    if (escaped) {
      current += char;
      escaped = false;
      continue;
    }

    if (char === '\\') {
      escaped = true;
      continue;
    }

    if (char === '|') {
      cells.push(current.trim());
      current = '';
      continue;
    }

    current += char;
  }

  cells.push(current.trim());
  return cells;
}

function getHeadingLevel(line: string) {
  let level = 0;
  while (level < 4 && line[level] === '#') level++;

  return level > 0 && line[level] === ' ' ? level : 0;
}
