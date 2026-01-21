import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "IRIS - Research Collaborator Finder",
  description: "Find research collaborators at KSU and the Southeast consortium. AI-powered matching across 208K+ researchers.",
  keywords: ["research", "collaboration", "KSU", "Kennesaw State University", "academic", "grants", "consortium"],
  authors: [{ name: "Kennesaw State University" }],
  creator: "KSU BrainLab",
  publisher: "Kennesaw State University",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "IRIS",
  },
  formatDetection: {
    telephone: false,
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://iris.kennesaw.edu",
    siteName: "IRIS - Research Collaborator Finder",
    title: "IRIS - Research Collaborator Finder",
    description: "Find research collaborators at KSU and the Southeast consortium. AI-powered matching across 208K+ researchers.",
  },
  twitter: {
    card: "summary_large_image",
    title: "IRIS - Research Collaborator Finder",
    description: "Find research collaborators at KSU and the Southeast consortium.",
  },
  icons: {
    icon: [
      { url: "/favicon.ico" },
      { url: "/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [
      { url: "/apple-touch-icon.png", sizes: "180x180" },
    ],
  },
};

export const viewport: Viewport = {
  themeColor: "#FDBB30",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="IRIS" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
