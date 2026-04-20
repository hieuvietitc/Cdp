"use client";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, CartesianGrid,
} from "recharts";

function ChartSkeleton() {
  return <Skeleton className="h-48 w-full" />;
}

export default function DashboardPage() {
  const { data: growth, isLoading: loadingGrowth } = useQuery({
    queryKey: ["profile-growth"],
    queryFn: () => analyticsApi.profileGrowth(90).then((r) => r.data),
  });
  const { data: topDest, isLoading: loadingDest } = useQuery({
    queryKey: ["top-destinations"],
    queryFn: () => analyticsApi.topDestinations(90).then((r) => r.data),
  });
  const { data: funnel, isLoading: loadingFunnel } = useQuery({
    queryKey: ["funnel"],
    queryFn: () =>
      analyticsApi.funnel("page_view,booking_started,booking_completed", 30).then((r) => r.data),
  });

  const maxFunnelUsers = funnel?.[0]?.users || 1;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Tổng quan</h1>
        <p className="text-muted-foreground text-sm mt-1">Hiệu suất hệ thống 90 ngày gần nhất</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Khách hàng mới (90 ngày)</CardTitle>
          </CardHeader>
          <CardContent>
            {loadingGrowth ? (
              <ChartSkeleton />
            ) : (
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={growth || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="day" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                  <YAxis tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                  <Tooltip
                    contentStyle={{
                      background: "hsl(var(--popover))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "var(--radius)",
                      fontSize: 12,
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="new_profiles"
                    name="Khách mới"
                    stroke="hsl(var(--primary))"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Top điểm đến (90 ngày)</CardTitle>
          </CardHeader>
          <CardContent>
            {loadingDest ? (
              <ChartSkeleton />
            ) : (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={topDest || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="destination" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                  <YAxis tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                  <Tooltip
                    contentStyle={{
                      background: "hsl(var(--popover))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "var(--radius)",
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="bookings" name="Lượt đặt" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Funnel đặt tour (30 ngày)</CardTitle>
          </CardHeader>
          <CardContent>
            {loadingFunnel ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => <Skeleton key={i} className="h-8 w-full" />)}
              </div>
            ) : (
              <div className="space-y-3">
                {(funnel || []).map((step: { step: string; users: number }, i: number) => {
                  const pct = ((step.users / maxFunnelUsers) * 100).toFixed(1);
                  return (
                    <div key={i} className="flex items-center gap-4">
                      <span className="text-sm text-muted-foreground w-48 shrink-0">{step.step}</span>
                      <div className="flex-1 bg-muted rounded-full h-5 overflow-hidden">
                        <div
                          className="bg-primary h-full rounded-full transition-all"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="text-sm font-semibold w-24 text-right tabular-nums">
                        {step.users.toLocaleString("vi-VN")}
                      </span>
                      <span className="text-xs text-muted-foreground w-12 text-right">{pct}%</span>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
