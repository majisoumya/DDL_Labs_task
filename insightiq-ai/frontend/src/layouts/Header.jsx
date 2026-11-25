import React, { useState } from "react";
import { Menu, Calendar, Bell, ShieldCheck, Zap } from "lucide-react";
import { DataQualityModal } from "../components/common";

export const Header = ({ onOpenSidebar, title = "Overview" }) => {
  const [showQualityModal, setShowQualityModal] = useState(false);

  return (
    <>
      <header
        data-testid="app-header"
        className="h-16 bg-surface border-b border-surface-border px-6 flex items-center justify-between sticky top-0 z-30 shadow-subtle"
      >
        {/* Left: Mobile Toggle & Page Title */}
        <div className="flex items-center gap-4">
          <button
            onClick={onOpenSidebar}
            aria-label="Open sidebar"
            className="p-2 -ml-2 text-navy-700 hover:bg-surface-muted rounded-lg md:hidden"
          >
            <Menu size={20} />
          </button>
          <div>
            <h1 className="text-base font-semibold text-navy-900 tracking-tight">
              {title}
            </h1>
            <p className="text-[11px] text-navy-600 hidden sm:block">
              Autonomous Business Intelligence & Analytics
            </p>
          </div>
        </div>

        {/* Right: Controls & Badges */}
        <div className="flex items-center gap-3">
          {/* Date Filter Badge */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-surface-subtle border border-surface-border rounded-lg text-xs font-medium text-navy-700">
            <Calendar size={14} className="text-navy-600" />
            <span>FY 2024 (Jan – Jun)</span>
          </div>

          {/* Security / Governance Data Quality Trigger */}
          <button
            onClick={() => setShowQualityModal(true)}
            title="Inspect live dataset quality and audit records"
            data-testid="data-quality-trigger"
            className="flex items-center gap-1.5 px-2.5 py-1.5 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200/80 rounded-lg text-xs font-semibold text-emerald-800 transition-colors"
          >
            <ShieldCheck size={14} className="text-emerald-600" />
            <span className="hidden md:inline">Audited Ground Truth</span>
          </button>

          {/* Real-time Indicator */}
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-brand-50 border border-brand-100 rounded-lg text-xs font-semibold text-brand-700">
            <Zap size={14} className="text-brand-600 fill-brand-600" />
            <span className="hidden lg:inline">Autonomous Engine</span>
          </div>
        </div>
      </header>

      {/* Dataset Quality Modal */}
      <DataQualityModal
        isOpen={showQualityModal}
        onClose={() => setShowQualityModal(false)}
      />
    </>
  );
};

export default Header;
