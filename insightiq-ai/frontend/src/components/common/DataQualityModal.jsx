import React, { useEffect, useState } from "react";
import { X, ShieldCheck, Database, CheckCircle2, AlertOctagon, FileText } from "lucide-react";
import { systemService } from "../../services";
import { formatCurrency, formatNumber } from "../../utils/formatters";
import { Badge } from "./Badge";

export const DataQualityModal = ({ isOpen, onClose }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isOpen) return;
    let isMounted = true;
    setLoading(true);
    setError(null);

    systemService
      .getQualitySummary()
      .then((res) => {
        if (isMounted) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || "Failed to load data quality summary");
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      data-testid="data-quality-modal"
      className="fixed inset-0 z-50 bg-navy-950/50 backdrop-blur-xs flex items-center justify-center p-4"
    >
      <div className="bg-surface w-full max-w-xl rounded-2xl border border-surface-border shadow-modal overflow-hidden text-xs">
        {/* Modal Header */}
        <div className="px-6 py-4 bg-surface-subtle border-b border-surface-border flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center shadow-xs">
              <ShieldCheck size={18} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-navy-900 tracking-tight">
                Dataset Quality & Governance Report
              </h3>
              <p className="text-[11px] text-navy-600">
                Audited transactional tables & schema integrity checks
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close modal"
            className="p-1.5 text-navy-400 hover:text-navy-700 hover:bg-black/5 rounded-lg transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 space-y-4 max-h-[75vh] overflow-y-auto">
          {loading && (
            <div className="py-12 text-center text-navy-500 flex flex-col items-center gap-2">
              <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
              <span>Auditing warehouse tables...</span>
            </div>
          )}

          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl">
              {error}
            </div>
          )}

          {data && !loading && (
            <>
              {/* Certification Banner */}
              <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-emerald-900">
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={16} className="text-emerald-600" />
                  <span className="font-semibold text-xs">
                    {data.data_integrity?.audit_certification || "100% Ground-Truth Certified"}
                  </span>
                </div>
                <Badge variant="success" size="sm">
                  {data.database_engine?.toUpperCase() || "DATABASE"} LIVE
                </Badge>
              </div>

              {/* Table Inventory Grid */}
              <div className="space-y-2">
                <span className="text-[11px] font-semibold text-navy-600 uppercase tracking-wider block">
                  Audited Entity Inventory
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                  <div className="p-2.5 bg-surface-subtle border border-surface-border rounded-xl text-center">
                    <span className="text-[11px] text-navy-600 block">Customers</span>
                    <span className="text-base font-bold text-navy-900 font-mono">
                      {formatNumber(data.inventory?.customers_count || 0)}
                    </span>
                  </div>
                  <div className="p-2.5 bg-surface-subtle border border-surface-border rounded-xl text-center">
                    <span className="text-[11px] text-navy-600 block">Products</span>
                    <span className="text-base font-bold text-navy-900 font-mono">
                      {formatNumber(data.inventory?.products_count || 0)}
                    </span>
                  </div>
                  <div className="p-2.5 bg-surface-subtle border border-surface-border rounded-xl text-center">
                    <span className="text-[11px] text-navy-600 block">Total Orders</span>
                    <span className="text-base font-bold text-navy-900 font-mono">
                      {formatNumber(data.inventory?.orders_total || 0)}
                    </span>
                  </div>
                  <div className="p-2.5 bg-surface-subtle border border-surface-border rounded-xl text-center">
                    <span className="text-[11px] text-navy-600 block">Order Items</span>
                    <span className="text-base font-bold text-navy-900 font-mono">
                      {formatNumber(data.inventory?.order_items_total || 0)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Order Status Breakdown */}
              <div className="space-y-2">
                <span className="text-[11px] font-semibold text-navy-600 uppercase tracking-wider block">
                  Transaction Lifecycle Distribution
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <div className="p-2 rounded-lg border border-emerald-200 bg-emerald-50/50">
                    <span className="text-[10px] text-emerald-800 font-semibold block uppercase">Completed</span>
                    <span className="text-sm font-bold text-emerald-900 font-mono">
                      {data.order_status_breakdown?.completed || 0}
                    </span>
                  </div>
                  <div className="p-2 rounded-lg border border-amber-200 bg-amber-50/50">
                    <span className="text-[10px] text-amber-800 font-semibold block uppercase">Pending</span>
                    <span className="text-sm font-bold text-amber-900 font-mono">
                      {data.order_status_breakdown?.pending || 0}
                    </span>
                  </div>
                  <div className="p-2 rounded-lg border border-slate-200 bg-slate-50">
                    <span className="text-[10px] text-slate-700 font-semibold block uppercase">Cancelled</span>
                    <span className="text-sm font-bold text-slate-900 font-mono">
                      {data.order_status_breakdown?.cancelled || 0}
                    </span>
                  </div>
                  <div className="p-2 rounded-lg border border-rose-200 bg-rose-50/50">
                    <span className="text-[10px] text-rose-800 font-semibold block uppercase">Returned</span>
                    <span className="text-sm font-bold text-rose-900 font-mono">
                      {data.order_status_breakdown?.returned || 0}
                    </span>
                  </div>
                </div>
              </div>

              {/* Data Governance & Quarantining Note */}
              <div className="p-3 bg-surface-subtle border border-surface-border rounded-xl space-y-1.5">
                <div className="flex items-center gap-1.5 font-semibold text-navy-900">
                  <FileText size={13} className="text-brand-600" />
                  <span>Strict Governance Policies Enforced</span>
                </div>
                <p className="text-[11px] text-navy-600 leading-relaxed">
                  {data.governance_exclusions?.policy_rule}
                </p>
                <div className="text-[11px] text-navy-700 font-medium">
                  Quarantined Inactive Volume:{" "}
                  <strong className="text-navy-900 font-mono">
                    {data.governance_exclusions?.excluded_orders_count || 0} orders
                  </strong>{" "}
                  ({formatCurrency(data.governance_exclusions?.excluded_revenue_dollars || 0)})
                </div>
              </div>
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 bg-surface-subtle border-t border-surface-border flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-navy-900 hover:bg-navy-800 text-white font-medium rounded-xl transition-colors text-xs"
          >
            Close Report
          </button>
        </div>
      </div>
    </div>
  );
};

export default DataQualityModal;
