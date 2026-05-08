'use client';

import { memo, useCallback, useEffect, useState } from 'react';

import { useBiddingStore } from '@/store/bidding';

import BiddingDraftTab from './BiddingDraftTab';
import BiddingEvidenceTab from './BiddingEvidenceTab';
import BiddingExecuteTab from './BiddingExecuteTab';
import BiddingFilesTab from './BiddingFilesTab';
import BiddingPlanTab from './BiddingPlanTab';
import BiddingReviewTab from './BiddingReviewTab';

const TABS = [
  { key: 'files', label: 'Files' },
  { key: 'plan', label: 'Plan' },
  { key: 'execute', label: 'Execute' },
  { key: 'review', label: 'Review' },
  { key: 'draft', label: 'Draft' },
  { key: 'evidence', label: 'Evidence' },
] as const;

type TabKey = (typeof TABS)[number]['key'];

const BiddingWorkbench = memo(() => {
  const [activeTab, setActiveTab] = useState<TabKey>('files');

  const {
    health,
    projects,
    currentProject,
    workflowLoading,
    workflowError,
    planResult,
    executeResult,
    reviewResult,
    artifacts,
    currentArtifact,
    currentArtifactName,
    currentEvidenceTrace,
    artifactLoading,
    evidenceResults,
    evidenceLoading,
    demoRunning,
    fetchHealth,
    fetchProjects,
    createNewProject,
    selectProject,
    uploadProjectFile,
    runPlanAction,
    approvePlanAction,
    runExecuteAction,
    runReviewAction,
    fetchArtifactContent,
    searchEvidenceAction,
    runDemo,
    clearError,
  } = useBiddingStore();

  useEffect(() => {
    fetchHealth();
    fetchProjects();
  }, [fetchHealth, fetchProjects]);

  const [newProjectName, setNewProjectName] = useState('');

  const handleCreateProject = useCallback(async () => {
    if (!newProjectName.trim()) return;
    try {
      const id = await createNewProject(newProjectName.trim());
      setNewProjectName('');
      await selectProject(id);
    } catch {
      return;
    }
  }, [newProjectName, createNewProject, selectProject]);

  const projectId = currentProject?.id;

  const handleRunPlan = useCallback(
    () => projectId && runPlanAction(projectId),
    [projectId, runPlanAction],
  );
  const handleApprovePlan = useCallback(
    () => projectId && approvePlanAction(projectId),
    [projectId, approvePlanAction],
  );
  const handleRunExecute = useCallback(
    () => projectId && runExecuteAction(projectId),
    [projectId, runExecuteAction],
  );
  const handleRunReview = useCallback(
    () => projectId && runReviewAction(projectId),
    [projectId, runReviewAction],
  );
  const handleRunDemo = useCallback(async () => {
    const demoProjectId = await runDemo();
    if (demoProjectId) setActiveTab('draft');
  }, [runDemo]);

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'system-ui, sans-serif' }}>
      {/* Left: Chat area placeholder */}
      <div
        style={{
          width: '40%',
          borderRight: '1px solid #e5e5e5',
          display: 'flex',
          flexDirection: 'column',
          background: '#fafafa',
        }}
      >
        <div
          style={{ padding: 16, borderBottom: '1px solid #e5e5e5', fontWeight: 600, fontSize: 16 }}
        >
          Bidding Assistant
        </div>
        <div style={{ flex: 1, padding: 16, overflowY: 'auto' }}>
          <div style={{ marginBottom: 12, color: '#666', fontSize: 13 }}>
            {health ? (
              <span>
                API: {health.status} | Evidence: {health.evidence_count} items | Projects:{' '}
                {health.project_count}
              </span>
            ) : (
              <span style={{ color: '#c00' }}>API not connected</span>
            )}
          </div>

          {/* Project list */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontWeight: 500, marginBottom: 8 }}>Projects</div>
            {projects.map((p) => (
              <div
                key={p.id}
                style={{
                  padding: '8px 12px',
                  cursor: 'pointer',
                  background: currentProject?.id === p.id ? '#e6f4ff' : 'transparent',
                  borderRadius: 6,
                  marginBottom: 4,
                  fontSize: 13,
                }}
                onClick={() => selectProject(p.id)}
              >
                <div>
                  {p.name} <span style={{ color: '#999' }}>({p.stage})</span>
                </div>
                {p.readiness_summary && (
                  <div aria-label="Project Readiness" style={{ marginTop: 6 }}>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                      <MiniBadge color="#52c41a">
                        A {p.readiness_summary.attachment_ready}/
                        {p.readiness_summary.attachment_total}
                      </MiniBadge>
                      <MiniBadge
                        color={
                          p.readiness_summary.attachment_needs_page_hint > 0 ? '#faad14' : '#52c41a'
                        }
                      >
                        {p.readiness_summary.attachment_needs_page_hint} attach
                      </MiniBadge>
                      <MiniBadge color="#1677ff">
                        S {p.readiness_summary.scoring_ready}/{p.readiness_summary.scoring_total}
                      </MiniBadge>
                      <MiniBadge
                        color={
                          p.readiness_summary.scoring_needs_page_hint > 0 ||
                          p.readiness_summary.scoring_needs_bidder_evidence > 0
                            ? '#faad14'
                            : '#52c41a'
                        }
                      >
                        {p.readiness_summary.scoring_needs_page_hint +
                          p.readiness_summary.scoring_needs_bidder_evidence}{' '}
                        scoring
                      </MiniBadge>
                      <MiniBadge color="#13c2c2">
                        C {p.readiness_summary.commercial_ready}/
                        {p.readiness_summary.commercial_total}
                      </MiniBadge>
                      <MiniBadge
                        color={
                          p.readiness_summary.commercial_needs_page_hint > 0 ||
                          p.readiness_summary.commercial_tender_only > 0
                            ? '#faad14'
                            : '#52c41a'
                        }
                      >
                        {p.readiness_summary.commercial_needs_page_hint +
                          p.readiness_summary.commercial_tender_only}{' '}
                        commercial
                      </MiniBadge>
                      <MiniBadge color="#722ed1">
                        K {p.readiness_summary.contract_ready}/{p.readiness_summary.contract_total}
                      </MiniBadge>
                      <MiniBadge
                        color={
                          p.readiness_summary.contract_needs_page_hint > 0 ||
                          p.readiness_summary.contract_tender_only > 0
                            ? '#faad14'
                            : '#52c41a'
                        }
                      >
                        {p.readiness_summary.contract_needs_page_hint +
                          p.readiness_summary.contract_tender_only}{' '}
                        contract
                      </MiniBadge>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* New project */}
          <div style={{ marginBottom: 16 }}>
            <input
              placeholder="New project name..."
              value={newProjectName}
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #d9d9d9',
                borderRadius: 6,
                fontSize: 13,
              }}
              onChange={(e) => setNewProjectName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCreateProject()}
            />
            <button
              disabled={workflowLoading || !newProjectName.trim()}
              style={{
                marginTop: 8,
                width: '100%',
                padding: '8px 16px',
                background: '#1677ff',
                color: '#fff',
                border: 'none',
                borderRadius: 6,
                cursor: 'pointer',
                fontSize: 13,
              }}
              onClick={handleCreateProject}
            >
              Create Project
            </button>
          </div>

          {/* Quick commands */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontWeight: 500, marginBottom: 8 }}>Real Case</div>
            <CommandBtn
              label="Demo Real Case"
              loading={demoRunning}
              style={{ background: '#722ed1' }}
              onClick={handleRunDemo}
            />
          </div>

          {currentProject && (
            <div>
              <div style={{ fontWeight: 500, marginBottom: 8 }}>Quick Commands</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                <CommandBtn
                  label="Analyze / Plan"
                  loading={workflowLoading}
                  onClick={handleRunPlan}
                />
                <CommandBtn
                  label="Approve Plan"
                  loading={workflowLoading}
                  onClick={handleApprovePlan}
                />
                <CommandBtn label="Execute" loading={workflowLoading} onClick={handleRunExecute} />
                <CommandBtn label="Review" loading={workflowLoading} onClick={handleRunReview} />
              </div>
            </div>
          )}

          {/* Error display */}
          {workflowError && (
            <div
              style={{
                marginTop: 12,
                padding: '8px 12px',
                background: '#fff2f0',
                border: '1px solid #ffccc7',
                borderRadius: 6,
                fontSize: 12,
                color: '#cf1322',
              }}
            >
              {workflowError}
              <span style={{ float: 'right', cursor: 'pointer' }} onClick={clearError}>
                x
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Right: Workbench */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Tab bar */}
        <div
          style={{
            display: 'flex',
            borderBottom: '1px solid #e5e5e5',
            background: '#fff',
          }}
        >
          {TABS.map((tab) => (
            <div
              key={tab.key}
              style={{
                padding: '12px 20px',
                cursor: 'pointer',
                fontWeight: activeTab === tab.key ? 600 : 400,
                borderBottom: activeTab === tab.key ? '2px solid #1677ff' : '2px solid transparent',
                color: activeTab === tab.key ? '#1677ff' : '#666',
                fontSize: 14,
              }}
              onClick={() => setActiveTab(tab.key)}
            >
              {tab.label}
            </div>
          ))}
        </div>

        {/* Tab content */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
          {!currentProject ? (
            <EmptyState message="Select or create a project to begin" />
          ) : (
            <>
              {activeTab === 'files' && (
                <BiddingFilesTab
                  loading={workflowLoading}
                  project={currentProject}
                  onUpload={uploadProjectFile}
                />
              )}
              {activeTab === 'plan' && (
                <BiddingPlanTab planResult={planResult} project={currentProject} />
              )}
              {activeTab === 'execute' && (
                <BiddingExecuteTab executeResult={executeResult} project={currentProject} />
              )}
              {activeTab === 'review' && (
                <BiddingReviewTab project={currentProject} reviewResult={reviewResult} />
              )}
              {activeTab === 'draft' && (
                <BiddingDraftTab
                  artifacts={artifacts}
                  currentArtifact={currentArtifact}
                  currentArtifactName={currentArtifactName}
                  currentEvidenceTrace={currentEvidenceTrace}
                  loading={artifactLoading}
                  projectId={currentProject.id}
                  materialGroups={
                    currentProject.review?.material_groups ??
                    currentProject.execution?.material_groups ??
                    []
                  }
                  onFetchArtifact={fetchArtifactContent}
                />
              )}
              {activeTab === 'evidence' && (
                <BiddingEvidenceTab
                  loading={evidenceLoading}
                  results={evidenceResults}
                  onSearch={searchEvidenceAction}
                />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
});

BiddingWorkbench.displayName = 'BiddingWorkbench';

function CommandBtn({
  label,
  onClick,
  loading,
  style,
}: {
  label: string;
  onClick: () => void;
  loading?: boolean;
  style?: React.CSSProperties;
}) {
  return (
    <button
      disabled={loading}
      style={{
        padding: '6px 12px',
        background: '#1677ff',
        color: '#fff',
        border: 'none',
        borderRadius: 4,
        cursor: loading ? 'wait' : 'pointer',
        fontSize: 12,
        opacity: loading ? 0.6 : 1,
        ...style,
      }}
      onClick={onClick}
    >
      {loading ? '...' : label}
    </button>
  );
}

function MiniBadge({ children, color }: { children: React.ReactNode; color: string }) {
  return (
    <span
      style={{
        background: `${color}18`,
        borderRadius: 4,
        color,
        display: 'inline-block',
        fontSize: 11,
        fontWeight: 500,
        lineHeight: '16px',
        padding: '0 5px',
      }}
    >
      {children}
    </span>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
        color: '#999',
        fontSize: 14,
      }}
    >
      {message}
    </div>
  );
}

export default BiddingWorkbench;
