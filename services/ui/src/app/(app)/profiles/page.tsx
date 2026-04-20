"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { profilesApi } from "@/lib/api";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Search, ChevronRight } from "lucide-react";

const TIER_VARIANT: Record<string, "default" | "secondary" | "success" | "warning" | "destructive" | "outline"> = {
  platinum: "default",
  gold: "warning",
  silver: "secondary",
  bronze: "outline",
};

export default function ProfilesPage() {
  const [search, setSearch] = useState("");
  const [q, setQ] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["profiles", q],
    queryFn: () => profilesApi.list(q ? { q } : {}).then((r) => r.data),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Hồ sơ khách hàng</h1>
        <p className="text-muted-foreground text-sm mt-1">Tìm kiếm và xem thông tin khách hàng</p>
      </div>

      <form
        onSubmit={(e) => { e.preventDefault(); setQ(search); }}
        className="flex gap-2 max-w-xl"
      >
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="email:nguyen@gmail.com | phone:+849 | loyalty_id:123"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Button type="submit">Tìm kiếm</Button>
      </form>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-3">
              {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Email</TableHead>
                    <TableHead>Điện thoại</TableHead>
                    <TableHead>Tier</TableHead>
                    <TableHead className="text-right">Tổng chi (VND)</TableHead>
                    <TableHead className="w-10" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(data?.items || []).length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-muted-foreground py-10">
                        Không tìm thấy khách hàng nào
                      </TableCell>
                    </TableRow>
                  ) : (
                    (data?.items || []).map((p: Record<string, unknown>) => {
                      const traits = p.traits as Record<string, unknown>;
                      const tier = (traits?.tier as string) || "";
                      return (
                        <TableRow key={p.id as string}>
                          <TableCell>{(p.email as string) || <span className="text-muted-foreground">—</span>}</TableCell>
                          <TableCell>{(p.phone as string) || <span className="text-muted-foreground">—</span>}</TableCell>
                          <TableCell>
                            {tier ? (
                              <Badge variant={TIER_VARIANT[tier.toLowerCase()] || "outline"}>
                                {tier}
                              </Badge>
                            ) : (
                              <span className="text-muted-foreground">—</span>
                            )}
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {(traits?.total_spend_vnd as number)?.toLocaleString("vi-VN") || "—"}
                          </TableCell>
                          <TableCell>
                            <Link href={`/profiles/${p.id}`}>
                              <Button variant="ghost" size="icon">
                                <ChevronRight className="h-4 w-4" />
                              </Button>
                            </Link>
                          </TableCell>
                        </TableRow>
                      );
                    })
                  )}
                </TableBody>
              </Table>
              <div className="px-4 py-3 border-t text-sm text-muted-foreground">
                Tổng: <span className="font-medium text-foreground">{(data?.total || 0).toLocaleString()}</span> khách hàng
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
