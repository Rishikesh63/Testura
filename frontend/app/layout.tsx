import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "sonner";

export const metadata: Metadata = {
  title: "Testura — AI Testing for Vibe-Coded Apps",
  description:
    "Connect your GitHub repo. Testura reads your code, generates tests, runs them, and tells you what broke — zero manual work required.",
  metadataBase: new URL("https://www.testura.dev"),
  keywords: ["AI testing", "automated testing", "vibe coding", "GitHub", "Jest", "pytest", "code quality"],
  authors: [{ name: "Testura" }],
  openGraph: {
    title: "Testura — AI writes and runs tests for your code",
    description:
      "Connect your GitHub repo. Testura reads your code, generates tests, runs them, and tells you what broke — zero manual work required.",
    url: "https://www.testura.dev",
    siteName: "Testura",
    images: [{ url: "/og", width: 1200, height: 630, alt: "Testura — AI Testing" }],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Testura — AI writes and runs tests for your code",
    description:
      "Connect your GitHub repo. AI generates and runs tests automatically. 84% average pass rate.",
    images: ["/og.png"],
  },
  robots: { index: true, follow: true },
  icons: { icon: "/favicon.ico" },
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
