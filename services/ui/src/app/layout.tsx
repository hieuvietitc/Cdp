import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "CDP Admin",
  description: "Customer Data Platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const runtimeConfig = {
    apiUrl: process.env.API_URL ?? "http://localhost:4002",
    collectorUrl: process.env.COLLECTOR_URL ?? "http://localhost:4001",
  };

  return (
    <html lang="vi">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `window.__CDP_CONFIG__ = ${JSON.stringify(runtimeConfig)};`,
          }}
        />
      </head>
      <body className="bg-background text-foreground antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
