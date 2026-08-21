"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Overview" },
  { href: "/cohort/", label: "Cohorts" },
  { href: "/baseline/", label: "Baseline" },
  { href: "/exposure/", label: "Exposure–response" },
  { href: "/interaction/", label: "Interaction" },
  { href: "/sensitivity/", label: "Sensitivity" },
  { href: "/provenance/", label: "Provenance" },
];

export function SiteFrame({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const current = pathname.endsWith("/") || pathname === "" ? pathname : `${pathname}/`;

  return (
    <>
      <header className="site-header">
        <div className="site-header-inner">
          <p className="site-kicker">Aggregate tables only</p>
          <p className="site-title">
            <Link href="/">Heat-exposure / cryopreserved donor-sperm analysis</Link>
          </p>
          <p className="site-sub">
            Local viewer for grouped statistics. Individual donor records are not in this
            repository and are not served by these pages.
          </p>
          <nav className="site-nav" aria-label="Datasets">
            {NAV.map((item) => {
              const active = item.href === "/" ? current === "/" : current.startsWith(item.href);
              return (
                <Link key={item.href} href={item.href} aria-current={active ? "page" : undefined}>
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>
      <main>{children}</main>
      <footer className="site-footer">
        <div className="site-footer-inner">
          <p>
            Unpublished research. Figures and coefficients are copied from{" "}
            <code>web/public/data/</code>; nothing is estimated in the browser.
          </p>
          <p>
            Donor-level tables stay on the analysis host. See the repository{" "}
            <code>DATA_POLICY.md</code>.
          </p>
        </div>
      </footer>
    </>
  );
}
