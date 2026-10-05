import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DHANRASHI // VASP-Trace Forensics & Attribution Suite (SIH26182)",
  description:
    "Sovereign Blockchain Intelligence, Multi-Hop Fluid Flow Attribution, and Law Enforcement VASP Data Dispatch.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-surface font-body-md text-on-surface antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}

