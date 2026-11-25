import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  TrendingUp,
  Package,
  Users,
  Bot,
  Layers,
  Database,
  ChevronRight,
  Sparkles,
} from "lucide-react";

const NAV_ITEMS = [
  {
    name: "Executive Overview",
    path: "/",
    icon: LayoutDashboard,
    badge: null,
  },
  {
    name: "Sales Analytics",
    path: "/sales",
    icon: TrendingUp,
    badge: null,
  },
  {
    name: "Product Catalog",
    path: "/products",
    icon: Package,
    badge: null,
  },
  {
    name: "Customer Cohorts",
    path: "/customers",
    icon: Users,
    badge: null,
  },
  {
    name: "AI Analyst Studio",
    path: "/analyst",
    icon: Bot,
    badge: "AI",
  },
];

export const Sidebar = ({ isOpen, onClose }) => {
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          data-testid="sidebar-backdrop"
          onClick={onClose}
          className="fixed inset-0 bg-navy-950/60 backdrop-blur-sm z-40 md:hidden"
        />
      )}

      {/* Sidebar Container */}
      <aside
        data-testid="app-sidebar"
        className={`fixed md:static inset-y-0 left-0 z-50 w-64 bg-navy-900 text-surface flex flex-col justify-between border-r border-navy-800 transition-transform duration-200 ease-in-out ${
          isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
      >
        {/* Brand Header */}
        <div>
          <div className="h-16 px-6 flex items-center gap-3 border-b border-navy-800">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-brand-600 to-brand-500 flex items-center justify-center shadow-md">
              <Sparkles size={20} className="text-white" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-base tracking-tight text-white">
                  InsightIQ
                </span>
                <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-brand-500/20 text-brand-400 border border-brand-500/30">
                  AI
                </span>
              </div>
              <p className="text-[11px] text-navy-600">Enterprise BI Platform</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1">
            <div className="px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-navy-600">
              Analytics Domains
            </div>
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.path === "/"}
                  onClick={() => onClose && onClose()}
                  className={({ isActive }) =>
                    `flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-colors ${
                      isActive
                        ? "bg-brand-600 text-white shadow-sm"
                        : "text-slate-300 hover:bg-navy-800 hover:text-white"
                    }`
                  }
                >
                  <div className="flex items-center gap-3">
                    <Icon size={18} />
                    <span>{item.name}</span>
                  </div>
                  {item.badge && (
                    <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-brand-500/30 text-brand-300">
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Warehouse Health & Footer */}
        <div className="p-4 border-t border-navy-800">
          <div className="p-3 rounded-lg bg-navy-950/60 border border-navy-800/80 flex items-center gap-3">
            <div className="relative">
              <Database size={16} className="text-brand-400" />
              <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-emerald-500 ring-2 ring-navy-950" />
            </div>
            <div className="text-[11px]">
              <div className="font-semibold text-slate-200">PostgreSQL Live</div>
              <div className="text-slate-400">Ground-Truth Grounded</div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
