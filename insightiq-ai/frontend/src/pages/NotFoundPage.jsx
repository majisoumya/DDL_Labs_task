import React from "react";
import { Link } from "react-router-dom";
import { Home, AlertTriangle } from "lucide-react";

export const NotFoundPage = () => {
  return (
    <div
      data-testid="not-found-page"
      className="min-h-[60vh] flex flex-col items-center justify-center text-center p-6"
    >
      <div className="w-14 h-14 rounded-2xl bg-amber-50 border border-amber-200 text-amber-600 flex items-center justify-center mb-4">
        <AlertTriangle size={28} />
      </div>
      <h2 className="text-xl font-bold text-navy-900 tracking-tight">
        404 — Page Not Found
      </h2>
      <p className="text-xs text-navy-600 max-w-sm mt-1 mb-6">
        The analytics view you are attempting to access does not exist or has been relocated.
      </p>
      <Link
        to="/"
        className="inline-flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
      >
        <Home size={14} />
        Return to Executive Overview
      </Link>
    </div>
  );
};

export default NotFoundPage;
