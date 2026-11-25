import React, { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";
import Header from "./Header";

const ROUTE_TITLES = {
  "/": "Executive BI Overview",
  "/sales": "Sales Performance & Trends",
  "/products": "Catalog & Product Performance",
  "/customers": "Customer Cohort Intelligence",
  "/analyst": "AI Analyst Studio",
};

export const AppLayout = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const location = useLocation();

  const currentTitle = ROUTE_TITLES[location.pathname] || "Executive Intelligence";

  return (
    <div
      data-testid="app-layout"
      className="min-h-screen bg-surface-subtle flex flex-col md:flex-row font-sans"
    >
      {/* Sidebar Navigation */}
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header
          onOpenSidebar={() => setIsSidebarOpen(true)}
          title={currentTitle}
        />

        <main
          data-testid="main-content"
          className="flex-1 p-6 md:p-8 overflow-y-auto max-w-7xl w-full mx-auto"
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
