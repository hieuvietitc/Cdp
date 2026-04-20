"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { sourcesApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, PieChart, Pie, Cell, Legend,
} from "recharts";
import {
  ArrowLeft, Copy, Check, RefreshCw, AlertTriangle,
  Code2, BarChart2,
} from "lucide-react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogFooter, DialogDescription,
} from "@/components/ui/dialog";

const COLLECTOR_URL =
  process.env.NEXT_PUBLIC_COLLECTOR_URL || "http://localhost:8001";

const PIE_COLORS = [
  "hsl(var(--primary))",
  "#06b6d4", "#8b5cf6", "#f59e0b", "#10b981",
  "#ef4444", "#ec4899", "#84cc16", "#f97316", "#6366f1",
];

function buildSnippet(writeKey: string) {
  return `<!-- CDP Tracking Snippet — dán vào <head> của website -->
<script>
!function(){
  var cdp=window.cdp=window.cdp||[];
  if(cdp.initialized)return;
  cdp.initialized=true;
  cdp.methods=["track","page","identify","consent","reset"];
  cdp.factory=function(m){return function(){var a=Array.prototype.slice.call(arguments);a.unshift(m);cdp.push(a);return cdp}};
  for(var i=0;i<cdp.methods.length;i++){var k=cdp.methods[i];cdp[k]=cdp.factory(k)}
  cdp.load=function(writeKey,opts){
    cdp._writeKey=writeKey;cdp._opts=opts||{};
    var s=document.createElement("script");
    s.type="text/javascript";s.async=true;
    s.src=(opts&&opts.collectorUrl||"${COLLECTOR_URL}")+"/sdk/cdp.min.js";
    var f=document.getElementsByTagName("script")[0];
    f.parentNode.insertBefore(s,f);
  };
  cdp.load("${writeKey}", { collectorUrl: "${COLLECTOR_URL}" });
  cdp.page();
}();
</script>`;
}

const USAGE_EXAMPLE = `// Sau khi khách đăng nhập:
cdp.identify("loyalty_member_123", {
  email: "nguyen@example.com",
  phone: "+84912345678",
  full_name: "Nguyễn Văn An",
  tier: "gold"
});

// Khi khách đặt tour:
cdp.track("booking_completed", {
  booking_id: "VT-2025-001",
  destination: "Đà Nẵng",
  total_price_vnd: 7000000,
  departure_date: "2025-12-25"
});

// Khi khách logout:
cdp.reset();`;

export default function SourceDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const qc = useQueryClient();
  const [copied, setCopied] = useState<"snippet" | "key" | null>(null);
  const [confirmRotate, setConfirmRotate] = useState(false);

  const { data: source, isLoading } = useQuery({
    queryKey: ["source", params.id],
    queryFn: () => sourcesApi.get(params.id).then((r) => r.data),
  });

  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ["source-stats", params.id],
    queryFn: () => sourcesApi.stats(params.id).then((r) => r.data),
    enabled: !!source,
  });

  const rotateMutation = useMutation({
    mutationFn: () => sourcesApi.rotateKey(params.id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["source", params.id] });
      qc.invalidateQueries({ queryKey: ["sources"] });
      setConfirmRotate(false);
    },
  });

  function copy(text: string, type: "snippet" | "key") {
    navigator.clipboard.writeText(text);
    setCopied(type);
    setTimeout(() => setCopied(null), 2000);
  }

  if (isLoading) {
    return (
      <div className="max-w-4xl space-y-4">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!source) return <div className="text-muted-foreground">Không tìm thấy nguồn dữ liệu</div>;

  const snippet = buildSnippet(source.write_key);

  return (
    <div className="max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => router.push("/sources")}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">{source.name}</h1>
            <Badge variant={source.is_active ? "success" : "outline"}>
              {source.is_active ? "Hoạt động" : "Tắt"}
            </Badge>
            <Badge variant="secondary">{source.type}</Badge>
          </div>
          <p className="text-muted-foreground text-sm mt-0.5">
            Tạo lúc {new Date(source.created_at).toLocaleDateString("vi-VN")}
          </p>
        </div>
      </div>

      {/* Write key bar */}
      <Card>
        <CardContent className="py-4 flex items-center justify-between gap-4">
          <div>
            <p className="text-xs text-muted-foreground mb-1">Write Key</p>
            <code className="text-sm font-mono bg-muted px-2 py-1 rounded select-all">
              {source.write_key}
            </code>
          </div>
          <div className="flex gap-2 shrink-0">
            <Button
              variant="outline" size="sm"
              onClick={() => copy(source.write_key, "key")}
            >
              {copied === "key" ? <Check className="h-3.5 w-3.5 mr-1.5" /> : <Copy className="h-3.5 w-3.5 mr-1.5" />}
              {copied === "key" ? "Đã copy" : "Copy key"}
            </Button>
            <Button
              variant="outline" size="sm"
              onClick={() => setConfirmRotate(true)}
            >
              <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
              Đổi key
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs defaultValue="install">
        <TabsList>
          <TabsTrigger value="install">
            <Code2 className="h-3.5 w-3.5 mr-2" />
            Cài đặt
          </TabsTrigger>
          <TabsTrigger value="stats">
            <BarChart2 className="h-3.5 w-3.5 mr-2" />
            Thống kê
          </TabsTrigger>
        </TabsList>

        {/* ── Install tab ── */}
        <TabsContent value="install" className="space-y-4 mt-4">
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base">Bước 1 — Dán snippet vào &lt;head&gt;</CardTitle>
                  <CardDescription>Copy đoạn code này và dán vào thẻ &lt;head&gt; của mọi trang</CardDescription>
                </div>
                <Button variant="outline" size="sm" onClick={() => copy(snippet, "snippet")}>
                  {copied === "snippet"
                    ? <><Check className="h-3.5 w-3.5 mr-1.5" />Đã copy</>
                    : <><Copy className="h-3.5 w-3.5 mr-1.5" />Copy snippet</>}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <pre className="bg-zinc-950 text-zinc-100 text-xs rounded-lg p-4 overflow-x-auto leading-relaxed font-mono whitespace-pre">
                {snippet}
              </pre>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Bước 2 — Gọi các phương thức tracking</CardTitle>
              <CardDescription>Thêm vào code JavaScript của website (không dán vào snippet)</CardDescription>
            </CardHeader>
            <CardContent>
              <pre className="bg-zinc-950 text-zinc-100 text-xs rounded-lg p-4 overflow-x-auto leading-relaxed font-mono whitespace-pre">
                {USAGE_EXAMPLE}
              </pre>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Kiểm tra hoạt động</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-muted-foreground">
              <p>Sau khi nhúng, mở browser DevTools → Network và tìm requests đến <code className="bg-muted px-1 rounded">{COLLECTOR_URL}/v1/events</code></p>
              <p>Hoặc vào trang <strong>Hồ sơ khách hàng</strong> để thấy profile ẩn danh được tạo tự động.</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Stats tab ── */}
        <TabsContent value="stats" className="space-y-4 mt-4">
          {loadingStats ? (
            <div className="space-y-3">
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-64 w-full" />
            </div>
          ) : (
            <>
              {/* Summary */}
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardContent className="p-4">
                    <p className="text-xs text-muted-foreground">Tổng sự kiện</p>
                    <p className="text-2xl font-bold mt-1">
                      {(stats?.total_events || 0).toLocaleString("vi-VN")}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <p className="text-xs text-muted-foreground">Loại sự kiện (30 ngày)</p>
                    <p className="text-2xl font-bold mt-1">
                      {stats?.top_event_types?.length || 0}
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Events per day chart */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Sự kiện theo ngày (30 ngày qua)</CardTitle>
                </CardHeader>
                <CardContent>
                  {(stats?.daily || []).length === 0 ? (
                    <div className="h-40 flex items-center justify-center text-muted-foreground text-sm">
                      Chưa có dữ liệu
                    </div>
                  ) : (
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart data={stats.daily}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis
                          dataKey="day"
                          tick={{ fontSize: 10 }}
                          tickFormatter={(v) => v.slice(5)}
                          stroke="hsl(var(--muted-foreground))"
                        />
                        <YAxis tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" />
                        <Tooltip
                          contentStyle={{
                            background: "hsl(var(--popover))",
                            border: "1px solid hsl(var(--border))",
                            borderRadius: "var(--radius)",
                            fontSize: 12,
                          }}
                          labelFormatter={(v) => `Ngày ${v}`}
                        />
                        <Bar dataKey="events" name="Sự kiện" fill="hsl(var(--primary))" radius={[3, 3, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </CardContent>
              </Card>

              {/* Event type breakdown */}
              {(stats?.top_event_types || []).length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base">Phân loại sự kiện (30 ngày qua)</CardTitle>
                  </CardHeader>
                  <CardContent className="flex items-center gap-6">
                    <ResponsiveContainer width={200} height={200}>
                      <PieChart>
                        <Pie
                          data={stats.top_event_types}
                          dataKey="count"
                          nameKey="event_name"
                          cx="50%"
                          cy="50%"
                          outerRadius={80}
                        >
                          {stats.top_event_types.map((_: unknown, i: number) => (
                            <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            background: "hsl(var(--popover))",
                            border: "1px solid hsl(var(--border))",
                            borderRadius: "var(--radius)",
                            fontSize: 12,
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="flex-1 space-y-2">
                      {stats.top_event_types.map((t: { event_name: string; count: number }, i: number) => (
                        <div key={t.event_name} className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-2">
                            <div
                              className="h-2.5 w-2.5 rounded-full shrink-0"
                              style={{ background: PIE_COLORS[i % PIE_COLORS.length] }}
                            />
                            <span className="font-mono text-xs">{t.event_name}</span>
                          </div>
                          <span className="tabular-nums font-medium">{t.count.toLocaleString("vi-VN")}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </TabsContent>
      </Tabs>

      {/* Rotate key confirm dialog */}
      <Dialog open={confirmRotate} onOpenChange={setConfirmRotate}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              Đổi Write Key?
            </DialogTitle>
            <DialogDescription>
              Key cũ sẽ bị vô hiệu hoá ngay lập tức. Bạn cần cập nhật snippet trên website sau khi đổi.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmRotate(false)}>Huỷ</Button>
            <Button
              variant="destructive"
              onClick={() => rotateMutation.mutate()}
              disabled={rotateMutation.isPending}
            >
              {rotateMutation.isPending ? "Đang đổi..." : "Xác nhận đổi key"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
