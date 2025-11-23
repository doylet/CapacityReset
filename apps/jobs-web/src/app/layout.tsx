import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Jobs Skills Explorer",
  description: "View and edit job skills with ML enrichment",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
