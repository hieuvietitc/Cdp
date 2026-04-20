"use client";
import { useQuery } from "@tanstack/react-query";
import { profilesApi } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { User, Mail, Phone, Calendar } from "lucide-react";

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs text-muted-foreground mb-1">{label}</p>
        <p className="text-lg font-semibold">{value}</p>
      </CardContent>
    </Card>
  );
}

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

  if (isLoading) {
    return (
      <div className="space-y-4 max-w-4xl">
        <Skeleton className="h-16 w-80" />
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-20" />)}
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (!profile) {
    return <div className="text-muted-foreground">Không tìm thấy hồ sơ</div>;
  }

  const traits = profile.traits || {};
  const fullName = traits.full_name || "Khách hàng";
  const initials = fullName
    .split(" ")
    .slice(-2)
    .map((w: string) => w[0])
    .join("")
    .toUpperCase();

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Avatar className="h-14 w-14">
          <AvatarFallback className="text-lg bg-primary text-primary-foreground">{initials}</AvatarFallback>
        </Avatar>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{fullName}</h1>
          <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
            {profile.email && (
              <span className="flex items-center gap-1"><Mail className="h-3.5 w-3.5" />{profile.email}</span>
            )}
            {profile.phone && (
              <span className="flex items-center gap-1"><Phone className="h-3.5 w-3.5" />{profile.phone}</span>
            )}
          </div>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label="Tier" value={traits.tier || "—"} />
        <StatCard
          label="Tổng chi tiêu"
          value={traits.total_spend_vnd
            ? `${Number(traits.total_spend_vnd).toLocaleString("vi-VN")} đ`
            : "—"}
        />
        <StatCard
          label="Điểm loyalty"
          value={traits.loyalty_points ? Number(traits.loyalty_points).toLocaleString() : "—"}
        />
        <StatCard
          label="Số đơn"
          value={traits.booking_count ? String(traits.booking_count) : "—"}
        />
      </div>

      {/* Tabs: Segments + Events + Traits */}
      <Tabs defaultValue="events">
        <TabsList>
          <TabsTrigger value="events">Sự kiện ({(events || []).length})</TabsTrigger>
          <TabsTrigger value="segments">Phân khúc ({(segments || []).length})</TabsTrigger>
          <TabsTrigger value="traits">Thuộc tính</TabsTrigger>
        </TabsList>

        <TabsContent value="events">
          <Card>
            <ScrollArea className="h-80">
              <div className="p-4 space-y-2">
                {(events || []).length === 0 ? (
                  <p className="text-muted-foreground text-sm text-center py-8">Chưa có sự kiện nào</p>
                ) : (
                  (events || []).map((e: Record<string, unknown>, i: number) => (
                    <div key={e.id as string}>
                      <div className="flex items-center justify-between py-1.5">
                        <div className="flex items-center gap-2">
                          <div className="h-2 w-2 rounded-full bg-primary" />
                          <span className="text-sm font-medium">{e.event_name as string}</span>
                        </div>
                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {new Date(e.occurred_at as string).toLocaleDateString("vi-VN")}
                        </span>
                      </div>
                      {i < (events || []).length - 1 && <Separator />}
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>
          </Card>
        </TabsContent>

        <TabsContent value="segments">
          <Card>
            <CardContent className="p-4">
              {(segments || []).length === 0 ? (
                <p className="text-muted-foreground text-sm text-center py-8">Chưa thuộc phân khúc nào</p>
              ) : (
                <div className="space-y-2">
                  {(segments || []).map((s: Record<string, unknown>) => (
                    <div key={s.id as string} className="flex items-center justify-between py-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary">{s.name as string}</Badge>
                      </div>
                      <span className="text-sm text-muted-foreground">
                        {(s.member_count as number)?.toLocaleString()} thành viên
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="traits">
          <Card>
            <CardContent className="p-4">
              <div className="grid grid-cols-2 gap-x-8 gap-y-2">
                {Object.entries(traits).map(([k, v]) => (
                  <div key={k} className="flex justify-between py-1.5 border-b last:border-0 text-sm">
                    <span className="text-muted-foreground font-mono">{k}</span>
                    <span className="font-medium text-right max-w-40 truncate">
                      {String(v)}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
