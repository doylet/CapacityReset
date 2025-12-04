import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Jobs Skills Explorer | ML-Powered Job Analysis",
    template: "%s | Jobs Skills Explorer",
  },
  description: "Explore and analyze job postings with AI-powered skills extraction and enrichment. Browse jobs, manage skills, and discover insights with machine learning.",
  keywords: ["jobs", "skills", "machine learning", "AI", "career", "analysis", "job search"],
  authors: [{ name: "CapacityReset Team" }],
  creator: "CapacityReset",
  publisher: "CapacityReset",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://jobs.capacityreset.com",
    title: "Jobs Skills Explorer | ML-Powered Job Analysis",
    description: "Explore and analyze job postings with AI-powered skills extraction and enrichment.",
    siteName: "Jobs Skills Explorer",
  },
  twitter: {
    card: "summary_large_image",
    title: "Jobs Skills Explorer",
    description: "AI-powered job analysis and skills management platform.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased font-sans">
        {children}
      </body>
    </html>
  );
}
