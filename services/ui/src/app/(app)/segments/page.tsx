"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { segmentsApi } from "@/lib/api";
import Link from "next/link";

export default function SegmentsPage() {
  const qc = useQueryClient();
  const { data: segments, isLoading } = useQuery({
    queryKey: ["segments"],
    queryFn: () => segmentsApi.list().then((r) => r.data),
  });

  const computeMutation = useMutation({
    mutationFn: (id: string) => segmentsApi.compute(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["segments"] }),
  });

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Phân khúc khách hàng</h1>
        <Link href="/segments/new" className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
          + Tạo phân khúc
        </Link>
      </div>

      {isLoading ? (
        <div className="text-gray-500">Đang tải...</div>
      ) : (
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Tên</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Thành viên</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Lần cập nhật</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Lịch refresh</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y">
              {(segments || []).map((s: Record<string, unknown>) => (
                <tr key={s.id as string} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{s.name as string}</td>
                  <td className="px-4 py-3">{(s.member_count as number)?.toLocaleString()}</td>
                  <td className="px-4 py-3 text-gray-500">
                    {s.last_computed ? new Date(s.last_computed as string).toLocaleString("vi-VN") : "Chưa chạy"}
                  </td>
                  <td className="px-4 py-3 text-gray-500">{s.refresh_cron as string}</td>
                  <td className="px-4 py-3 flex gap-2">
                    <button
                      onClick={() => computeMutation.mutate(s.id as string)}
                      className="text-blue-600 hover:underline text-xs"
                    >
                      Refresh
                    </button>
                    <Link href={`/segments/${s.id}`} className="text-gray-500 hover:underline text-xs">
                      Chi tiết
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
