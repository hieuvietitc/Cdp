"use client";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts";

export default function DashboardPage() {
  const { data: growth } = useQuery({
    queryKey: ["profile-growth"],
    queryFn: () => analyticsApi.profileGrowth(90).then((r) => r.data),
  });
  const { data: topDest } = useQuery({
    queryKey: ["top-destinations"],
    queryFn: () => analyticsApi.topDestinations(90).then((r) => r.data),
  });
  const { data: funnel } = useQuery({
    queryKey: ["funnel"],
    queryFn: () =>
      analyticsApi.funnel("page_view,booking_started,booking_completed", 30).then((r) => r.data),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Tổng quan</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="text-base font-semibold mb-4">Khách hàng mới (90 ngày)</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={growth || []}>
              <XAxis dataKey="day" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="new_profiles" stroke="#2563eb" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="text-base font-semibold mb-4">Top điểm đến (90 ngày)</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={topDest || []}>
              <XAxis dataKey="destination" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="bookings" fill="#2563eb" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="text-base font-semibold mb-4">Funnel đặt tour (30 ngày)</h2>
          <div className="space-y-3">
            {(funnel || []).map((step: { step: string; users: number }, i: number) => (
              <div key={i} className="flex items-center gap-3">
                <span className="text-sm text-gray-500 w-40">{step.step}</span>
                <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
                  <div
                    className="bg-blue-500 h-full rounded-full"
                    style={{ width: `${funnel?.[0]?.users ? (step.users / funnel[0].users) * 100 : 0}%` }}
                  />
                </div>
                <span className="text-sm font-medium w-16 text-right">{step.users.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
