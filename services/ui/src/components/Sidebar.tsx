"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";

const NAV = [
  { href: "/dashboard", label: "Tổng quan" },
  { href: "/profiles", label: "Hồ sơ khách hàng" },
  { href: "/segments", label: "Phân khúc" },
  { href: "/activations", label: "Kích hoạt" },
  { href: "/sources", label: "Nguồn dữ liệu" },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-56 bg-white border-r min-h-screen flex flex-col py-6">
      <div className="px-6 mb-8">
        <span className="font-bold text-lg text-blue-600">CDP Admin</span>
      </div>
      <nav className="flex-1 px-3 space-y-1">
        {NAV.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={clsx(
              "block px-3 py-2 rounded-lg text-sm font-medium transition-colors",
              pathname.startsWith(item.href)
                ? "bg-blue-50 text-blue-700"
                : "text-gray-600 hover:bg-gray-100"
            )}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
