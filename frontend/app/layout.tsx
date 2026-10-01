import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import QueryProvider from "@/components/QueryProvider";
import "./globals.css";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
});

const outfit = Outfit({
  variable: "--font-heading",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Perin Devi Natyalayam | Kuchipudi Classical Dance School",
  description: "Join Perin Devi Natyalayam to learn the divine art of Kuchipudi. We offer courses for all levels across multiple branches.",
  keywords: ["Kuchipudi", "Dance School", "Classical Dance", "Perin Devi Natyalayam"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${outfit.variable} h-full antialiased dark`}>
      <body className="min-h-full flex flex-col bg-background text-foreground selection:bg-primary selection:text-primary-foreground">
        <QueryProvider>
          {children}
        </QueryProvider>
      </body>
    </html>
  );
}
