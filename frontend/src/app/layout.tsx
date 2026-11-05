import type { Metadata } from "next";
import { IBM_Plex_Mono, Inter } from "next/font/google";
import "./globals.css";

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  display: "swap",
  variable: "--font-plex-mono",
});

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Grandmaster Echo — Analysis Terminal",
  description:
    "A multi-agent chess analysis terminal. Ingest a player's games, retrieve tactical patterns with Qdrant, and inspect a grounded, evaluated scouting report.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${plexMono.variable} ${inter.variable}`}>
      <body className="min-h-screen bg-term-bg font-sans text-term-text antialiased">
        {children}
      </body>
    </html>
  );
}
