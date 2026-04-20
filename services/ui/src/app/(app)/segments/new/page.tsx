"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { segmentsApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { Plus, Trash2, ArrowLeft, Save, ChevronDown, ChevronUp } from "lucide-react";

// ── Types ────────────────────────────────────────────────────────────────────

type Condition = {
  id: string;
  field: string;
  op: string;
  value: string;
  time_window_days: string; // "" means no window
};

type RuleGroup = {
  operator: "AND" | "OR";
  conditions: Condition[];
};

// ── Field definitions ─────────────────────────────────────────────────────────

type FieldDef = {
  value: string;
  label: string;
  type: "text" | "number" | "select" | "none" | "event";
  options?: { value: string; label: string }[];
  group: string;
};

const FIELDS: FieldDef[] = [
  // Trait — numeric
  { value: "traits.total_spend_vnd", label: "Tổng chi tiêu (VND)", type: "number", group: "Hồ sơ" },
  { value: "traits.loyalty_points", label: "Điểm loyalty", type: "number", group: "Hồ sơ" },
  { value: "traits.booking_count", label: "Số lần đặt tour", type: "number", group: "Hồ sơ" },
  // Trait — select / text
  {
    value: "traits.tier",
    label: "Hạng thành viên",
    type: "select",
    options: [
      { value: "platinum", label: "Platinum" },
      { value: "gold", label: "Gold" },
      { value: "silver", label: "Silver" },
      { value: "bronze", label: "Bronze" },
    ],
    group: "Hồ sơ",
  },
  { value: "traits.preferred_destination", label: "Điểm đến yêu thích", type: "text", group: "Hồ sơ" },
  // Profile fields
  { value: "profile.email", label: "Có email", type: "none", group: "Thông tin" },
  { value: "profile.phone", label: "Có số điện thoại", type: "none", group: "Thông tin" },
  { value: "profile.loyalty_member_id", label: "Là thành viên loyalty", type: "none", group: "Thông tin" },
  // Events
  { value: "events.booking_completed", label: "Đã đặt tour", type: "event", group: "Sự kiện" },
  { value: "events.booking_started", label: "Bắt đầu đặt tour", type: "event", group: "Sự kiện" },
  { value: "events.page_view", label: "Xem trang", type: "event", group: "Sự kiện" },
];

// ops available per field type
const OPS_NUMERIC = [
  { value: "gt", label: "lớn hơn" },
  { value: "gte", label: "≥" },
  { value: "lt", label: "nhỏ hơn" },
  { value: "lte", label: "≤" },
  { value: "eq", label: "bằng" },
  { value: "neq", label: "khác" },
  { value: "exists", label: "tồn tại" },
  { value: "not_exists", label: "không tồn tại" },
];

const OPS_TEXT = [
  { value: "eq", label: "bằng" },
  { value: "neq", label: "khác" },
  { value: "contains", label: "chứa" },
  { value: "not_contains", label: "không chứa" },
  { value: "exists", label: "tồn tại" },
  { value: "not_exists", label: "không tồn tại" },
];

const OPS_SELECT = [
  { value: "eq", label: "là" },
  { value: "neq", label: "không phải" },
  { value: "exists", label: "tồn tại" },
  { value: "not_exists", label: "không tồn tại" },
];

const OPS_NONE = [
  { value: "exists", label: "tồn tại" },
  { value: "not_exists", label: "không tồn tại" },
];

const OPS_EVENT = [
  { value: "exists", label: "đã thực hiện" },
  { value: "not_exists", label: "chưa thực hiện" },
];

const TIME_WINDOWS = [
  { value: "", label: "bất kỳ lúc nào" },
  { value: "7", label: "7 ngày qua" },
  { value: "30", label: "30 ngày qua" },
  { value: "90", label: "90 ngày qua" },
  { value: "180", label: "6 tháng qua" },
  { value: "365", label: "1 năm qua" },
];

const CRON_PRESETS = [
  { value: "0 2 * * *", label: "Mỗi ngày lúc 2:00" },
  { value: "0 * * * *", label: "Mỗi giờ" },
  { value: "0 2 * * 1", label: "Mỗi thứ Hai lúc 2:00" },
  { value: "0 2 1 * *", label: "Mỗi đầu tháng lúc 2:00" },
];

// ── Helpers ───────────────────────────────────────────────────────────────────

function uid() {
  return Math.random().toString(36).slice(2);
}

function getFieldDef(field: string): FieldDef | undefined {
  return FIELDS.find((f) => f.value === field);
}

function getOps(fieldDef?: FieldDef) {
  if (!fieldDef) return OPS_TEXT;
  if (fieldDef.type === "number") return OPS_NUMERIC;
  if (fieldDef.type === "select") return OPS_SELECT;
  if (fieldDef.type === "none") return OPS_NONE;
  if (fieldDef.type === "event") return OPS_EVENT;
  return OPS_TEXT;
}

function needsValue(op: string) {
  return !["exists", "not_exists"].includes(op);
}

function buildRuleAST(group: RuleGroup): object {
  return {
    operator: group.operator,
    conditions: group.conditions.map((c) => {
      const isEvent = c.field.startsWith("events.");
      const cond: Record<string, unknown> = {
        field: c.field,
        op: c.op,
        value: needsValue(c.op) ? c.value || null : null,
      };
      if (isEvent && c.time_window_days) {
        cond.time_window = { last_n_days: parseInt(c.time_window_days) };
      }
      return cond;
    }),
  };
}

// ── Sub-components ────────────────────────────────────────────────────────────

function ConditionRow({
  cond,
  onChange,
  onDelete,
}: {
  cond: Condition;
  onChange: (updated: Condition) => void;
  onDelete: () => void;
}) {
  const fieldDef = getFieldDef(cond.field);
  const ops = getOps(fieldDef);
  const isEvent = cond.field.startsWith("events.");
  const showValue = needsValue(cond.op) && fieldDef?.type !== "none" && fieldDef?.type !== "event";

  return (
    <div className="flex flex-wrap items-center gap-2 p-3 bg-muted/30 rounded-lg border">
      {/* Field selector */}
      <Select
        value={cond.field}
        onValueChange={(v) => {
          const newDef = getFieldDef(v);
          const newOps = getOps(newDef);
          onChange({ ...cond, field: v, op: newOps[0].value, value: "" });
        }}
      >
        <SelectTrigger className="w-52 bg-background">
          <SelectValue placeholder="Chọn điều kiện..." />
        </SelectTrigger>
        <SelectContent>
          {["Hồ sơ", "Thông tin", "Sự kiện"].map((group) => (
            <div key={group}>
              <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">{group}</div>
              {FIELDS.filter((f) => f.group === group).map((f) => (
                <SelectItem key={f.value} value={f.value}>{f.label}</SelectItem>
              ))}
            </div>
          ))}
        </SelectContent>
      </Select>

      {/* Operator selector */}
      <Select
        value={cond.op}
        onValueChange={(v) => onChange({ ...cond, op: v, value: "" })}
      >
        <SelectTrigger className="w-40 bg-background">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {ops.map((o) => (
            <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Value input */}
      {showValue && (
        fieldDef?.type === "select" ? (
          <Select value={cond.value} onValueChange={(v) => onChange({ ...cond, value: v })}>
            <SelectTrigger className="w-36 bg-background">
              <SelectValue placeholder="Chọn..." />
            </SelectTrigger>
            <SelectContent>
              {fieldDef.options?.map((o) => (
                <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : (
          <Input
            className="w-40 bg-background"
            type={fieldDef?.type === "number" ? "number" : "text"}
            placeholder="Giá trị..."
            value={cond.value}
            onChange={(e) => onChange({ ...cond, value: e.target.value })}
          />
        )
      )}

      {/* Time window (events only) */}
      {isEvent && (
        <Select
          value={cond.time_window_days}
          onValueChange={(v) => onChange({ ...cond, time_window_days: v })}
        >
          <SelectTrigger className="w-40 bg-background">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {TIME_WINDOWS.map((t) => (
              <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      {/* Delete */}
      <Button variant="ghost" size="icon" onClick={onDelete} className="ml-auto shrink-0 text-muted-foreground hover:text-destructive">
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function NewSegmentPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [cron, setCron] = useState("0 2 * * *");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [group, setGroup] = useState<RuleGroup>({
    operator: "AND",
    conditions: [
      { id: uid(), field: "traits.tier", op: "eq", value: "", time_window_days: "" },
    ],
  });

  const createMutation = useMutation({
    mutationFn: async (runCompute: boolean) => {
      const payload = {
        name,
        description: description || undefined,
        rules: buildRuleAST(group),
        refresh_cron: cron,
      };
      const res = await segmentsApi.create(payload);
      const segId = res.data.id;
      if (runCompute) {
        await segmentsApi.compute(segId).catch(() => null);
      }
      return segId;
    },
    onSuccess: () => router.push("/segments"),
  });

  function addCondition() {
    setGroup((g) => ({
      ...g,
      conditions: [
        ...g.conditions,
        { id: uid(), field: "traits.tier", op: "eq", value: "", time_window_days: "" },
      ],
    }));
  }

  function updateCondition(id: string, updated: Condition) {
    setGroup((g) => ({
      ...g,
      conditions: g.conditions.map((c) => (c.id === id ? updated : c)),
    }));
  }

  function deleteCondition(id: string) {
    setGroup((g) => ({ ...g, conditions: g.conditions.filter((c) => c.id !== id) }));
  }

  const canSave = name.trim() && group.conditions.length > 0;

  // Live preview of the rule JSON for debugging
  const rulePreview = JSON.stringify(buildRuleAST(group), null, 2);

  return (
    <div className="max-w-3xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => router.push("/segments")}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Tạo phân khúc mới</h1>
          <p className="text-muted-foreground text-sm mt-0.5">Xây dựng điều kiện lọc khách hàng</p>
        </div>
      </div>

      {/* Basic info */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Thông tin cơ bản</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="seg-name">Tên phân khúc <span className="text-destructive">*</span></Label>
            <Input
              id="seg-name"
              placeholder="VD: Khách VIP đặt Đà Nẵng 6 tháng gần đây"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="seg-desc">Mô tả</Label>
            <Input
              id="seg-desc"
              placeholder="Mô tả ngắn về phân khúc này..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Rule builder */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Điều kiện lọc</CardTitle>
            {/* AND / OR toggle */}
            <div className="flex items-center gap-1 bg-muted rounded-lg p-1">
              {(["AND", "OR"] as const).map((op) => (
                <button
                  key={op}
                  onClick={() => setGroup((g) => ({ ...g, operator: op }))}
                  className={cn(
                    "px-3 py-1 rounded-md text-xs font-semibold transition-colors",
                    group.operator === op
                      ? "bg-background text-foreground shadow"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  {op === "AND" ? "Tất cả (AND)" : "Bất kỳ (OR)"}
                </button>
              ))}
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            {group.operator === "AND"
              ? "Khách hàng phải thoả TẤT CẢ điều kiện bên dưới"
              : "Khách hàng chỉ cần thoả MỘT trong các điều kiện bên dưới"}
          </p>
        </CardHeader>
        <CardContent className="space-y-2">
          {group.conditions.length === 0 && (
            <div className="text-center py-8 text-muted-foreground text-sm">
              Chưa có điều kiện nào. Thêm điều kiện để bắt đầu lọc.
            </div>
          )}

          {group.conditions.map((cond, i) => (
            <div key={cond.id}>
              {i > 0 && (
                <div className="flex items-center gap-2 my-1">
                  <Separator className="flex-1" />
                  <Badge variant="outline" className="text-xs font-mono shrink-0">
                    {group.operator}
                  </Badge>
                  <Separator className="flex-1" />
                </div>
              )}
              <ConditionRow
                cond={cond}
                onChange={(updated) => updateCondition(cond.id, updated)}
                onDelete={() => deleteCondition(cond.id)}
              />
            </div>
          ))}

          <Button variant="outline" size="sm" onClick={addCondition} className="w-full mt-2">
            <Plus className="h-4 w-4 mr-2" />
            Thêm điều kiện
          </Button>
        </CardContent>
      </Card>

      {/* Advanced: cron + rule JSON */}
      <Card>
        <button
          className="w-full flex items-center justify-between p-4 text-sm font-medium text-left"
          onClick={() => setShowAdvanced((v) => !v)}
        >
          <span>Cài đặt nâng cao</span>
          {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>

        {showAdvanced && (
          <CardContent className="pt-0 space-y-4 border-t">
            <div className="space-y-1.5 pt-4">
              <Label>Lịch tự động refresh</Label>
              <Select value={cron} onValueChange={setCron}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CRON_PRESETS.map((c) => (
                    <SelectItem key={c.value} value={c.value}>
                      {c.label} <span className="text-muted-foreground ml-2 font-mono text-xs">({c.value})</span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label>Rule JSON (preview)</Label>
              <pre className="bg-muted rounded-md p-3 text-xs font-mono overflow-auto max-h-48 text-muted-foreground">
                {rulePreview}
              </pre>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Error */}
      {createMutation.isError && (
        <p className="text-sm text-destructive">
          Có lỗi xảy ra: {(createMutation.error as Error)?.message}
        </p>
      )}

      {/* Actions */}
      <div className="flex items-center gap-3 pb-8">
        <Button
          onClick={() => createMutation.mutate(true)}
          disabled={!canSave || createMutation.isPending}
        >
          <Save className="h-4 w-4 mr-2" />
          {createMutation.isPending ? "Đang lưu..." : "Lưu và chạy ngay"}
        </Button>
        <Button
          variant="outline"
          onClick={() => createMutation.mutate(false)}
          disabled={!canSave || createMutation.isPending}
        >
          Lưu (không chạy)
        </Button>
        <Button variant="ghost" onClick={() => router.push("/segments")}>
          Huỷ
        </Button>
      </div>
    </div>
  );
}
