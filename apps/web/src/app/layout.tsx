import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "JusticeGuide — Indian Legal Q&A",
  description:
    "Ask questions about the Indian Penal Code (IPC) and Bharatiya Nyaya Sanhita (BNS) with citations.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
