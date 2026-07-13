"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

export type ChartMetricItem = {
  name: string;
  revenue: number;
  quantity: number;
};

export type ChartSalesAnalysis = {
  total_revenue: number;
  order_count: number;
  total_quantity: number;
  average_order_value: number;
  monthly_trend: ChartMetricItem[];
  region_ranking: ChartMetricItem[];
  category_ranking: ChartMetricItem[];
  salesperson_ranking: ChartMetricItem[];
  customer_mix: Record<string, number>;
};

const pieColors = ["#2563eb", "#059669", "#d97706", "#7c3aed", "#0f766e"];

export function AnalyticsCharts({ analysis }: { analysis: ChartSalesAnalysis | null }) {
  if (!analysis) {
    return (
      <section className="panel analytics-panel">
        <div className="panel-title">
          <span>A</span>
          <h2>销售分析图表</h2>
        </div>
        <div className="empty">确认执行后，这里会展示趋势、排行和客户结构。</div>
      </section>
    );
  }

  const customerMix = Object.entries(analysis.customer_mix).map(([name, value]) => ({
    name,
    value
  }));

  return (
    <section className="panel analytics-panel">
      <div className="panel-title">
        <span>A</span>
        <h2>销售分析图表</h2>
      </div>

      <div className="kpi-grid">
        <Kpi label="销售额" value={`¥${formatNumber(analysis.total_revenue)}`} />
        <Kpi label="订单数" value={`${analysis.order_count}`} />
        <Kpi label="销售件数" value={`${analysis.total_quantity}`} />
        <Kpi label="平均客单价" value={`¥${formatNumber(analysis.average_order_value)}`} />
      </div>

      <div className="chart-grid">
        <ChartCard title="月度销售趋势">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={analysis.monthly_trend} margin={{ top: 12, right: 18, bottom: 0, left: 0 }}>
              <CartesianGrid stroke="#e5eaf1" vertical={false} />
              <XAxis dataKey="name" tickLine={false} axisLine={false} />
              <YAxis tickLine={false} axisLine={false} width={72} />
              <Tooltip formatter={(value) => `¥${formatNumber(Number(value))}`} />
              <Line type="monotone" dataKey="revenue" name="销售额" stroke="#2563eb" strokeWidth={3} dot />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="区域销售排行">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={analysis.region_ranking} margin={{ top: 12, right: 18, bottom: 0, left: 0 }}>
              <CartesianGrid stroke="#e5eaf1" vertical={false} />
              <XAxis dataKey="name" tickLine={false} axisLine={false} />
              <YAxis tickLine={false} axisLine={false} width={72} />
              <Tooltip formatter={(value) => `¥${formatNumber(Number(value))}`} />
              <Bar dataKey="revenue" name="销售额" fill="#2563eb" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="品类销售排行">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={analysis.category_ranking} margin={{ top: 12, right: 18, bottom: 0, left: 0 }}>
              <CartesianGrid stroke="#e5eaf1" vertical={false} />
              <XAxis dataKey="name" tickLine={false} axisLine={false} />
              <YAxis tickLine={false} axisLine={false} width={72} />
              <Tooltip formatter={(value) => `¥${formatNumber(Number(value))}`} />
              <Bar dataKey="revenue" name="销售额" fill="#059669" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="销售员业绩排行">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={analysis.salesperson_ranking} margin={{ top: 12, right: 18, bottom: 0, left: 0 }}>
              <CartesianGrid stroke="#e5eaf1" vertical={false} />
              <XAxis dataKey="name" tickLine={false} axisLine={false} />
              <YAxis tickLine={false} axisLine={false} width={72} />
              <Tooltip formatter={(value) => `¥${formatNumber(Number(value))}`} />
              <Bar dataKey="revenue" name="销售额" fill="#d97706" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="客户类型占比">
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={customerMix}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="48%"
                outerRadius={82}
                label={({ name, value }) => `${name} ${Number(value).toFixed(1)}%`}
              >
                {customerMix.map((item, index) => (
                  <Cell key={item.name} fill={pieColors[index % pieColors.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => `${Number(value).toFixed(2)}%`} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </section>
  );
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <article className="kpi-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <article className="chart-card">
      <h3>{title}</h3>
      {children}
    </article>
  );
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("zh-CN", {
    maximumFractionDigits: 2
  }).format(value);
}
