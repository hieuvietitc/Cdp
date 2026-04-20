"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, sourcesApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import Link from "next/link";
import { Plus, Copy, Check, Globe, Smartphone, Server, Radio, ChevronRight } from "lucide-react";

const TYPE_ICON: Record<string, React.ElementType> = {
  web: Globe,
  ios: Smartphone,
  android: Smartphone,
  server: Server,
};

export default function SourcesPage() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [type, setType] = useState("web");
  const [copiedKey, setCopiedKey] = useState("");

  const { data: sources, isLoading } = useQuery({
    queryKey: ["sources"],
    queryFn: () => sourcesApi.list().then((r) => r.data),
  });

  const createMutation = useMutation({
    mutationFn: () => sourcesApi.create({ name, type }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sources"] });
      setOpen(false);
      setName("");
      setType("web");
    },
  });

  function copy(key: string) {
    navigator.clipboard.writeText(key);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(""), 2000);
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Nguồn dữ liệu</h1>
          <p className="text-muted-foreground text-sm mt-1">Quản lý SDK write keys</p>
        </div>

        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Thêm nguồn
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Thêm nguồn dữ liệu mới</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div className="space-y-1.5">
                <Label htmlFor="src-name">Tên nguồn</Label>
                <Input
                  id="src-name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Website chính"
                />
              </div>
              <div className="space-y-1.5">
                <Label>Loại</Label>
                <Select value={type} onValueChange={setType}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="web">Web</SelectItem>
                    <SelectItem value="ios">iOS</SelectItem>
                    <SelectItem value="android">Android</SelectItem>
                    <SelectItem value="server">Server-side</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setOpen(false)}>Huỷ</Button>
              <Button onClick={() => createMutation.mutate()} disabled={!name || createMutation.isPending}>
                {createMutation.isPending ? "Đang tạo..." : "Tạo nguồn"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2].map((i) => <Skeleton key={i} className="h-20 w-full" />)}
        </div>
      ) : (sources || []).length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Radio className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
            <p className="text-muted-foreground">Chưa có nguồn dữ liệu nào</p>
            <p className="text-sm text-muted-foreground mt-1">Tạo nguồn để lấy write key cho SDK</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {(sources || []).map((s: Record<string, unknown>) => {
            const Icon = TYPE_ICON[s.type as string] || Radio;
            const isCopied = copiedKey === (s.write_key as string);
            return (
              <Card key={s.id as string}>
                <CardContent className="py-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-9 w-9 rounded-md bg-muted flex items-center justify-center">
                      <Icon className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div>
                      <p className="font-medium">{s.name as string}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <Badge variant="secondary" className="text-xs">{s.type as string}</Badge>
                        {s.is_active ? (
                          <Badge variant="success" className="text-xs">Hoạt động</Badge>
                        ) : (
                          <Badge variant="outline" className="text-xs">Tắt</Badge>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <code className="bg-muted text-xs px-3 py-1.5 rounded-md font-mono text-muted-foreground">
                      {s.write_key as string}
                    </code>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => copy(s.write_key as string)}
                      title="Copy write key"
                    >
                      {isCopied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                    </Button>
                    <Link href={`/sources/${s.id}`}>
                      <Button variant="ghost" size="icon" title="Xem snippet & thống kê">
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
