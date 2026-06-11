import type { ReactNode } from 'react';

interface PlaceholderViewProps {
  title: string;
  description: string;
  icon: ReactNode;
}

export const PlaceholderView = ({ title, description, icon }: PlaceholderViewProps) => (
  <div className="flex items-center justify-center h-full p-6">
    <div className="card p-12 text-center max-w-md">
      <div className="w-16 h-16 rounded-2xl bg-brand-light flex items-center justify-center mx-auto mb-4 text-brand">
        {icon}
      </div>
      <h2 className="text-xl font-bold text-slate-900 mb-2">{title}</h2>
      <p className="text-sm text-muted">{description}</p>
      <p className="text-xs text-muted mt-4 italic">Coming soon — will integrate with StrykeX platform</p>
    </div>
  </div>
);
