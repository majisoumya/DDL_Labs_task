import React from "react";
import { DollarSign, ShoppingCart, Users, TrendingUp } from "lucide-react";
import { MetricCard, CardSkeleton } from "../common";
import { formatCurrency, formatNumber } from "../../utils/formatters";

export const KpiGrid = ({ kpis = {}, loading = false, className = "" }) => {
  if (loading) {
    return (
      <div
        data-testid="kpi-grid-skeleton"
        className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 ${className}`}
      >
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
      </div>
    );
  }

  const {
    total_revenue = 0,
    total_orders = 0,
    total_customers = 0,
    repeat_customers = 0,
    average_order_value = 0,
  } = kpis;

  return (
    <div
      data-testid="kpi-grid"
      className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 ${className}`}
    >
      <MetricCard
        title="Total Revenue"
        value={formatCurrency(total_revenue)}
        subtext="Excluding returns & cancellations"
        icon={DollarSign}
        trend="positive"
      />
      <MetricCard
        title="Total Orders"
        value={formatNumber(total_orders)}
        subtext="Completed/Pending orders"
        icon={ShoppingCart}
      />
      <MetricCard
        title="Total Customers"
        value={formatNumber(total_customers)}
        subtext={`${formatNumber(repeat_customers)} repeat buyers`}
        icon={Users}
      />
      <MetricCard
        title="Average Order Value"
        value={formatCurrency(average_order_value)}
        subtext="Earned revenue per eligible order"
        icon={TrendingUp}
      />
    </div>
  );
};

export default KpiGrid;
