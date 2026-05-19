import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "sonner";

export const metadata: Metadata = {
  title: "Testura — AI Testing for Vibe-Coded Apps",
  description:
    "Connect your repo. AI writes and runs tests automatically. Zero manual work.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-sans antialiased">
        {children}
        <Toaster position="top-right" richColors />
      </body>
    </html>
  );
}
