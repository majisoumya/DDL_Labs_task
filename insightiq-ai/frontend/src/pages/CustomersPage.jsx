import React, { useState } from "react";
import { Users, UserCheck, UserX, Repeat } from "lucide-react";
import {
  MetricCard,
  Card,
  CardSkeleton,
  TableSkeleton,
  ErrorState,
  Badge,
} from "../components/common";
import { DateRangeFilter } from "../components/dashboard";
import { useAsync } from "../hooks/useAsync";
import { customerService, exportService } from "../services";
import { formatCurrency, formatNumber, formatPercentage } from "../utils/formatters";

export const CustomersPage = () => {
  const [dateRange, setDateRange] = useState({ startDate: "", endDate: "" });

  const {
    data: customerData,
    loading,
    error,
    retry,
  } = useAsync(async () => {
    const params = {
      start_date: dateRange.startDate || undefined,
      end_date: dateRange.endDate || undefined,
    };
    const [metrics, topCustomers, frequency] = await Promise.all([
      customerService.getCustomerMetrics(params),
      customerService.getTopCustomers({ limit: 10, ...params }),
      customerService.getCustomerOrderFrequency(params),
    ]);
    return { metrics, topCustomers, frequency };
  }, [dateRange.startDate, dateRange.endDate]);

  if (loading) {
    return (
      <div data-testid="customers-loading" className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
        <TableSkeleton rows={5} cols={5} />
      </div>
    );
  }

  if (error) {
    return (
      <div data-testid="customers-error" className="py-8">
        <ErrorState
          title="Could not load customer cohort intelligence"
          message={error}
          onRetry={retry}
        />
      </div>
    );
  }

  const { metrics, topCustomers = [], frequency = {} } = customerData || {};

  return (
    <div data-testid="customers-page" className="space-y-6">
      {/* Date Range Controls & Presets */}
      <DateRangeFilter
        startDate={dateRange.startDate}
        endDate={dateRange.endDate}
        onChange={setDateRange}
        onRefresh={retry}
        onExport={() =>
          exportService.downloadCustomersCsv({
            start_date: dateRange.startDate || undefined,
            end_date: dateRange.endDate || undefined,
          })
        }
      />
      {/* Customer KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Customers"
          value={formatNumber(metrics?.total_customers)}
          subtext="Registered customer database"
          icon={Users}
        />
        <MetricCard
          title="New Buyers (2024)"
          value={formatNumber(metrics?.new_customers)}
          subtext="First purchase in current period"
          icon={UserCheck}
        />
        <MetricCard
          title="Repeat Customers"
          value={formatNumber(metrics?.repeat_customers)}
          subtext={`${formatPercentage(metrics?.repeat_customer_rate)} retention rate`}
          icon={Repeat}
        />
        <MetricCard
          title="Inactive Accounts"
          value={formatNumber(metrics?.inactive_customers)}
          subtext="No purchases in 2024"
          icon={UserX}
        />
      </div>

      {/* Top Customer VIPs */}
      <Card
        title="High-Value Customers"
        subtitle="Ranked by cumulative monetary spend across eligible orders"
      >
        <div className="overflow-x-auto -mx-5 -my-5">
          <table className="w-full text-left text-xs">
            <thead className="bg-surface-subtle text-navy-600 font-semibold uppercase tracking-wider border-b border-surface-border">
              <tr>
                <th className="px-5 py-3">Customer</th>
                <th className="px-3 py-3">City</th>
                <th className="px-3 py-3 text-right">Orders</th>
                <th className="px-5 py-3 text-right">Total Spend</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border">
              {topCustomers.map((c, idx) => (
                <tr key={c.customer_id || idx} className="hover:bg-surface-subtle/60 transition-colors">
                  <td className="px-5 py-3 font-medium text-navy-900">{c.name}</td>
                  <td className="px-3 py-3 text-navy-600">{c.city || "—"}</td>
                  <td className="px-3 py-3 text-right font-mono text-navy-700">
                    {formatNumber(c.order_count)}
                  </td>
                  <td className="px-5 py-3 text-right font-semibold font-mono text-navy-900">
                    {formatCurrency(c.total_spend)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

export default CustomersPage;
