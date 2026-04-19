"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function SourcesPage() {
  const qc = useQueryClient();
  const [showNew, setShowNew] = useState(false);
  const [name, setName] = useState("");
  const [type, setType] = useState("web");
  const [copiedKey, setCopiedKey] = useState("");

  const { data: sources } = useQuery({
    queryKey: ["sources"],
    queryFn: () => api.get("/api/v1/sources").then((r) => r.data),
  });

  const createMutation = useMutation({
    mutationFn: () => api.post("/api/v1/sources", { name, type }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["sources"] }); setShowNew(false); setName(""); },
  });

  function copy(key: string) {
    navigator.clipboard.writeText(key);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(""), 2000);
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Nguồn dữ liệu (SDK)</h1>
        <button onClick={() => setShowNew(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
          + Thêm nguồn
        </button>
      </div>

      {showNew && (
        <div className="bg-white rounded-xl shadow p-6 mb-6">
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-1">Tên</label>
              <input value={name} onChange={(e) => setName(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="Website chính" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Loại</label>
              <select value={type} onChange={(e) => setType(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm">
                <option value="web">Web</option>
                <option value="ios">iOS</option>
                <option value="android">Android</option>
                <option value="server">Server</option>
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={() => createMutation.mutate()} disabled={!name} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">Tạo</button>
            <button onClick={() => setShowNew(false)} className="px-4 py-2 rounded-lg text-sm border hover:bg-gray-50">Huỷ</button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {(sources || []).map((s: Record<string, unknown>) => (
          <div key={s.id as string} className="bg-white rounded-xl shadow p-5 flex justify-between items-center">
            <div>
              <p className="font-medium">{s.name as string}</p>
              <p className="text-xs text-gray-500 mt-0.5">{s.type as string}</p>
            </div>
            <div className="flex items-center gap-3">
              <code className="bg-gray-100 text-xs px-3 py-1 rounded font-mono">{s.write_key as string}</code>
              <button onClick={() => copy(s.write_key as string)} className="text-blue-600 text-xs hover:underline">
                {copiedKey === s.write_key ? "Đã copy!" : "Copy"}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
