import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "多 Agent 自动化办公工作流平台",
  description: "企业办公场景的多 Agent 工作流技术展示"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
