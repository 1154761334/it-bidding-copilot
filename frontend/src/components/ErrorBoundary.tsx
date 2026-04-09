import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-surface p-12 text-center">
          <div className="w-24 h-24 bg-error/10 text-error rounded-3xl flex items-center justify-center mb-8">
            <span className="material-symbols-outlined text-5xl">warning</span>
          </div>
          <h1 className="text-3xl font-black tracking-tight text-primary mb-4">系统遇到预期外的波动</h1>
          <p className="text-secondary max-w-md mb-8 font-medium">
            AI 核心引擎在处理当前请求时发生了偏离。请尝试刷新页面或联系系统管理员。
          </p>
          <div className="bg-zinc-50 p-6 rounded-2xl border border-zinc-100 text-left mb-8 w-full max-w-lg">
             <p className="text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-2">Error Detail</p>
             <code className="text-xs text-error font-mono break-all line-clamp-3">
                {this.state.error?.message}
             </code>
          </div>
          <button 
            onClick={() => window.location.reload()}
            className="px-8 py-3 bg-primary text-on-primary rounded-xl font-bold hover:opacity-90 transition-all"
          >
            刷新并重试恢复
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
