"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { profilesApi } from "@/lib/api";
import Link from "next/link";

export default function ProfilesPage() {
  const [search, setSearch] = useState("");
  const [q, setQ] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["profiles", q],
    queryFn: () => profilesApi.list(q ? { q } : {}).then((r) => r.data),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Hồ sơ khách hàng</h1>

      <form
        onSubmit={(e) => { e.preventDefault(); setQ(search); }}
        className="flex gap-2 mb-6"
      >
        <input
          type="text"
          placeholder="email:nguyen@gmail.com | phone:+849 | loyalty_id:123"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
          Tìm
        </button>
      </form>

      {isLoading ? (
        <div className="text-gray-500">Đang tải...</div>
      ) : (
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Email</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Phone</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Tier</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Tổng chi (VND)</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y">
              {(data?.items || []).map((p: Record<string, unknown>) => (
                <tr key={p.id as string} className="hover:bg-gray-50">
                  <td className="px-4 py-3">{(p.email as string) || "—"}</td>
                  <td className="px-4 py-3">{(p.phone as string) || "—"}</td>
                  <td className="px-4 py-3">
                    {(p.traits as Record<string, string>)?.tier || "—"}
                  </td>
                  <td className="px-4 py-3">
                    {(p.traits as Record<string, number>)?.total_spend_vnd?.toLocaleString("vi-VN") || "—"}
                  </td>
                  <td className="px-4 py-3">
                    <Link href={`/profiles/${p.id}`} className="text-blue-600 hover:underline">
                      Chi tiết
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="px-4 py-3 text-sm text-gray-500 border-t">
            Tổng: {data?.total || 0} khách hàng
          </div>
        </div>
      )}
    </div>
  );
}
