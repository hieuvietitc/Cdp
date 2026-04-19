"use client";
import { useQuery } from "@tanstack/react-query";
import { profilesApi } from "@/lib/api";

export default function ProfileDetailPage({ params }: { params: { id: string } }) {
  const { data: profile, isLoading } = useQuery({
    queryKey: ["profile", params.id],
    queryFn: () => profilesApi.get(params.id).then((r) => r.data),
  });
  const { data: events } = useQuery({
    queryKey: ["profile-events", params.id],
    queryFn: () => profilesApi.events(params.id).then((r) => r.data),
    enabled: !!profile,
  });
  const { data: segments } = useQuery({
    queryKey: ["profile-segments", params.id],
    queryFn: () => profilesApi.segments(params.id).then((r) => r.data),
    enabled: !!profile,
  });

  if (isLoading) return <div className="text-gray-500">Đang tải...</div>;
  if (!profile) return <div>Không tìm thấy</div>;

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold mb-2">{profile.traits?.full_name || "Khách ẩn danh"}</h1>
      <p className="text-gray-500 text-sm mb-6">{profile.email} · {profile.phone}</p>

      <div className="grid grid-cols-3 gap-4 mb-6">
        {[
          { label: "Tier", value: profile.traits?.tier || "—" },
          { label: "Tổng chi", value: profile.traits?.total_spend_vnd ? `${Number(profile.traits.total_spend_vnd).toLocaleString("vi-VN")} đ` : "—" },
          { label: "Điểm loyalty", value: profile.traits?.loyalty_points?.toLocaleString() || "—" },
        ].map((s) => (
          <div key={s.label} className="bg-white rounded-xl shadow p-4">
            <p className="text-xs text-gray-500 mb-1">{s.label}</p>
            <p className="text-lg font-semibold">{s.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="font-semibold mb-3">Phân khúc</h2>
          {(segments || []).length === 0 ? (
            <p className="text-gray-400 text-sm">Chưa thuộc phân khúc nào</p>
          ) : (
            <ul className="space-y-2">
              {(segments || []).map((s: Record<string, unknown>) => (
                <li key={s.id as string} className="flex justify-between text-sm">
                  <span>{s.name as string}</span>
                  <span className="text-gray-400">{(s.member_count as number)?.toLocaleString()} thành viên</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="font-semibold mb-3">Lịch sử sự kiện</h2>
          <ul className="space-y-2 max-h-72 overflow-y-auto">
            {(events || []).map((e: Record<string, unknown>) => (
              <li key={e.id as string} className="text-sm flex justify-between">
                <span className="font-medium">{e.event_name as string}</span>
                <span className="text-gray-400">
                  {new Date(e.occurred_at as string).toLocaleDateString("vi-VN")}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
