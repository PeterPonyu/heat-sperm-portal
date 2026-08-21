import type { Metadata } from "next";
import { SiteFrame } from "@/components/SiteFrame";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Heat-exposure sperm analysis — aggregate tables",
    template: "%s — Heat-exposure sperm analysis",
  },
  description:
    "Static viewer for aggregate statistics from a heat-exposure and cryopreserved donor-sperm analysis. Individual-level records are not included.",
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <SiteFrame>{children}</SiteFrame>
      </body>
    </html>
  );
}
