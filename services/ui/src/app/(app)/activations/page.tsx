"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { activationsApi, destinationsApi, segmentsApi } from "@/lib/api";

export default function ActivationsPage() {
  const qc = useQueryClient();
  const [showNew, setShowNew] = useState(false);
  const [segmentId, setSegmentId] = useState("");
  const [destId, setDestId] = useState("");

  const { data: activations } = useQuery({
    queryKey: ["activations"],
    queryFn: () => activationsApi.list().then((r) => r.data),
  });
  const { data: segments } = useQuery({
    queryKey: ["segments"],
    queryFn: () => segmentsApi.list().then((r) => r.data),
  });
  const { data: destinations } = useQuery({
    queryKey: ["destinations"],
    queryFn: () => destinationsApi.list().then((r) => r.data),
  });

  const createMutation = useMutation({
    mutationFn: () => activationsApi.create({ segment_id: segmentId, destination_id: destId, trigger_type: "manual" }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["activations"] }); setShowNew(false); },
  });

  const STATUS_COLOR: Record<string, string> = {
    pending: "text-yellow-600 bg-yellow-50",
    running: "text-blue-600 bg-blue-50",
    completed: "text-green-600 bg-green-50",
    failed: "text-red-600 bg-red-50",
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Kích hoạt</h1>
        <button onClick={() => setShowNew(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
          + Tạo activation
        </button>
      </div>

      {showNew && (
        <div className="bg-white rounded-xl shadow p-6 mb-6">
          <h2 className="font-semibold mb-4">Tạo activation mới</h2>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-1">Phân khúc</label>
              <select value={segmentId} onChange={(e) => setSegmentId(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm">
                <option value="">-- chọn phân khúc --</option>
                {(segments || []).map((s: Record<string, unknown>) => (
                  <option key={s.id as string} value={s.id as string}>{s.name as string} ({(s.member_count as number)?.toLocaleString()})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Kênh kích hoạt</label>
              <select value={destId} onChange={(e) => setDestId(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm">
                <option value="">-- chọn kênh --</option>
                {(destinations || []).map((d: Record<string, unknown>) => (
                  <option key={d.id as string} value={d.id as string}>{d.name as string} ({d.type as string})</option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={() => createMutation.mutate()} disabled={!segmentId || !destId} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
              Chạy ngay
            </button>
            <button onClick={() => setShowNew(false)} className="px-4 py-2 rounded-lg text-sm border hover:bg-gray-50">
              Huỷ
            </button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">ID</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Trạng thái</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Đã gửi</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Thời gian</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {(activations || []).map((a: Record<string, unknown>) => (
              <tr key={a.id as string}>
                <td className="px-4 py-3 font-mono text-xs">{(a.id as string).slice(0, 8)}...</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${STATUS_COLOR[a.status as string] || ""}`}>
                    {a.status as string}
                  </span>
                </td>
                <td className="px-4 py-3">{(a.profiles_sent as number)?.toLocaleString()}</td>
                <td className="px-4 py-3 text-gray-500">
                  {a.created_at ? new Date(a.created_at as string).toLocaleString("vi-VN") : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
