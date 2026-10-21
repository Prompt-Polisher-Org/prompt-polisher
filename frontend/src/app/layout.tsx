import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/ui/ThemeProvider";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",   // Performance: show fallback font while Inter loads
  preload: true,
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",   // Performance: show fallback font while JetBrains Mono loads
  preload: false,    // Only preload primary font; mono is secondary
});

export const metadata: Metadata = {
  title: "Prompt Polisher | A workspace for clearer prompts",
  description:
    "Shape rough ideas into clearer AI prompts, keep conversations organized, and revisit your prompt work in one workspace.",
  keywords: ["AI prompts", "prompt engineering", "LLM", "RLHF", "prompt optimization"],
  openGraph: {
    title: "Prompt Polisher | AI Prompt Optimization",
    description: "A workspace to refine, organize, and revisit AI prompts.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    // suppressHydrationWarning: prevents React from warning about data-theme
    // mismatch between SSR (no attribute) and client (ThemeProvider sets it).
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${jetbrainsMono.variable} antialiased`}>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
