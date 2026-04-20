"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  Filter,
  Zap,
  Radio,
  LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard", label: "Tổng quan", icon: LayoutDashboard },
  { href: "/profiles", label: "Hồ sơ khách hàng", icon: Users },
  { href: "/segments", label: "Phân khúc", icon: Filter },
  { href: "/activations", label: "Kích hoạt", icon: Zap },
  { href: "/sources", label: "Nguồn dữ liệu", icon: Radio },
];

export function Sidebar() {
  const pathname = usePathname();

  function handleLogout() {
    localStorage.removeItem("cdp_token");
    window.location.href = "/login";
  }

  return (
    <aside className="w-60 bg-card border-r min-h-screen flex flex-col">
      <div className="px-6 py-5 border-b">
        <span className="font-bold text-lg text-primary">CDP Admin</span>
        <p className="text-xs text-muted-foreground mt-0.5">Travel Intelligence Platform</p>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
              pathname.startsWith(href)
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            )}
          >
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </Link>
        ))}
      </nav>

      <div className="px-3 py-4 border-t">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground w-full transition-colors"
        >
          <LogOut className="h-4 w-4" />
          Đăng xuất
        </button>
      </div>
    </aside>
  );
}
