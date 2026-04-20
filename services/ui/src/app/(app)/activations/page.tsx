"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { activationsApi, destinationsApi, segmentsApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Plus, Zap } from "lucide-react";

type StatusVariant = "default" | "secondary" | "success" | "warning" | "destructive" | "outline";

const STATUS_MAP: Record<string, { label: string; variant: StatusVariant }> = {
  pending: { label: "Đang chờ", variant: "warning" },
  running: { label: "Đang chạy", variant: "default" },
  completed: { label: "Hoàn thành", variant: "success" },
  completed_with_errors: { label: "Có lỗi", variant: "warning" },
  failed: { label: "Thất bại", variant: "destructive" },
};

export default function ActivationsPage() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [segmentId, setSegmentId] = useState("");
  const [destId, setDestId] = useState("");

  const { data: activations, isLoading } = useQuery({
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
    mutationFn: () =>
      activationsApi.create({ segment_id: segmentId, destination_id: destId, trigger_type: "manual" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["activations"] });
      setOpen(false);
      setSegmentId("");
      setDestId("");
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Kích hoạt</h1>
          <p className="text-muted-foreground text-sm mt-1">Push phân khúc đến các kênh marketing</p>
        </div>

        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Tạo activation
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Tạo activation mới</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div className="space-y-1.5">
                <Label>Phân khúc</Label>
                <Select value={segmentId} onValueChange={setSegmentId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Chọn phân khúc..." />
                  </SelectTrigger>
                  <SelectContent>
                    {(segments || []).map((s: Record<string, unknown>) => (
                      <SelectItem key={s.id as string} value={s.id as string}>
                        {s.name as string} ({(s.member_count as number)?.toLocaleString("vi-VN")} thành viên)
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Kênh kích hoạt</Label>
                <Select value={destId} onValueChange={setDestId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Chọn kênh..." />
                  </SelectTrigger>
                  <SelectContent>
                    {(destinations || []).map((d: Record<string, unknown>) => (
                      <SelectItem key={d.id as string} value={d.id as string}>
                        {d.name as string} — {d.type as string}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setOpen(false)}>Huỷ</Button>
              <Button
                onClick={() => createMutation.mutate()}
                disabled={!segmentId || !destId || createMutation.isPending}
              >
                <Zap className="h-4 w-4 mr-2" />
                {createMutation.isPending ? "Đang chạy..." : "Chạy ngay"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-3">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Trạng thái</TableHead>
                  <TableHead className="text-right">Đã gửi</TableHead>
                  <TableHead className="text-right">Lỗi</TableHead>
                  <TableHead>Thời gian</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(activations || []).length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-muted-foreground py-10">
                      Chưa có activation nào
                    </TableCell>
                  </TableRow>
                ) : (
                  (activations || []).map((a: Record<string, unknown>) => {
                    const status = STATUS_MAP[a.status as string] || { label: a.status as string, variant: "outline" as StatusVariant };
                    return (
                      <TableRow key={a.id as string}>
                        <TableCell>
                          <code className="text-xs text-muted-foreground">
                            {(a.id as string).slice(0, 8)}…
                          </code>
                        </TableCell>
                        <TableCell>
                          <Badge variant={status.variant}>{status.label}</Badge>
                        </TableCell>
                        <TableCell className="text-right tabular-nums">
                          {(a.profiles_sent as number)?.toLocaleString("vi-VN") || "0"}
                        </TableCell>
                        <TableCell className="text-right tabular-nums">
                          {(a.profiles_failed as number) > 0 ? (
                            <span className="text-destructive">{(a.profiles_failed as number).toLocaleString()}</span>
                          ) : "0"}
                        </TableCell>
                        <TableCell className="text-muted-foreground text-sm">
                          {a.created_at
                            ? new Date(a.created_at as string).toLocaleString("vi-VN")
                            : "—"}
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
