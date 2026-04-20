"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { segmentsApi } from "@/lib/api";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Plus, RefreshCw, ChevronRight, Users } from "lucide-react";

export default function SegmentsPage() {
  const qc = useQueryClient();
  const [refreshingId, setRefreshingId] = useState<string | null>(null);

  const { data: segments, isLoading } = useQuery({
    queryKey: ["segments"],
    queryFn: () => segmentsApi.list().then((r) => r.data),
  });

  const computeMutation = useMutation({
    mutationFn: async (id: string) => {
      setRefreshingId(id);
      return segmentsApi.compute(id);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["segments"] });
      setRefreshingId(null);
    },
    onError: () => setRefreshingId(null),
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Phân khúc khách hàng</h1>
          <p className="text-muted-foreground text-sm mt-1">Tạo và quản lý các nhóm khách hàng</p>
        </div>
        <Link href="/segments/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Tạo phân khúc
          </Button>
        </Link>
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-3">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tên phân khúc</TableHead>
                  <TableHead>Thành viên</TableHead>
                  <TableHead>Cập nhật lần cuối</TableHead>
                  <TableHead>Lịch refresh</TableHead>
                  <TableHead className="w-32" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {(segments || []).length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-muted-foreground py-10">
                      Chưa có phân khúc nào. Tạo phân khúc đầu tiên của bạn!
                    </TableCell>
                  </TableRow>
                ) : (
                  (segments || []).map((s: Record<string, unknown>) => (
                    <TableRow key={s.id as string}>
                      <TableCell>
                        <span className="font-medium">{s.name as string}</span>
                        {s.description && (
                          <p className="text-xs text-muted-foreground mt-0.5">{s.description as string}</p>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1.5">
                          <Users className="h-3.5 w-3.5 text-muted-foreground" />
                          <span className="tabular-nums">
                            {(s.member_count as number)?.toLocaleString("vi-VN") || "0"}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-muted-foreground text-sm">
                        {s.last_computed
                          ? new Date(s.last_computed as string).toLocaleString("vi-VN")
                          : <Badge variant="outline">Chưa chạy</Badge>}
                      </TableCell>
                      <TableCell>
                        {s.refresh_cron ? (
                          <code className="text-xs bg-muted px-1.5 py-0.5 rounded">
                            {s.refresh_cron as string}
                          </code>
                        ) : (
                          <span className="text-muted-foreground text-sm">Thủ công</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1 justify-end">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => computeMutation.mutate(s.id as string)}
                            disabled={refreshingId === (s.id as string)}
                          >
                            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${refreshingId === s.id ? "animate-spin" : ""}`} />
                            Refresh
                          </Button>
                          <Link href={`/segments/${s.id}`}>
                            <Button variant="ghost" size="icon">
                              <ChevronRight className="h-4 w-4" />
                            </Button>
                          </Link>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
