"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
export default function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="site-header">
        <div className="masthead">
          <Link href="/" className="brand" aria-label="Snap-2-Store home">
            <span className="brand-mark">
              s<span>2</span>s
            </span>
            <span>
              Snap-2-Store<small>THE CATALOG DARKROOM</small>
            </span>
          </Link>
          <nav aria-label="Main navigation">
            <Link className={path === "/create" ? "active" : ""} href="/create">
              The studio
            </Link>
            <Link className={path === "/bulk" ? "active" : ""} href="/bulk">
              Bulk desk
            </Link>
            <Link
              className={path === "/history" ? "active" : ""}
              href="/history"
            >
              Your ledger
            </Link>
            <Link
              className={path === "/under-the-hood" ? "active" : ""}
              href="/under-the-hood"
            >
              Under the hood
            </Link>
          </nav>
          <Link
            href="/settings"
            className="settings-link"
            aria-label="Integrations and settings"
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <path d="M4 7h16M4 17h16M8 4v6M16 14v6" />
            </svg>
            <span>Settings</span>
          </Link>
        </div>
        <div className="edition-line">
          <span>NEURALSHIFT / INDEPENDENT COMMERCE TOOLS</span>
          <span>PHOTO IN. DRAFT OUT. YOU DECIDE.</span>
        </div>
      </header>
      <main id="main">{children}</main>
      <footer className="site-footer">
        <Link href="/" className="footer-brand">
          Good products deserve
          <br />
          <em>a good first impression.</em>
        </Link>
        <div>
          <p>Made for the shop around the corner.</p>
          <p>
            <Link href="/impact">Calculate your time back ↗</Link>
          </p>
          <span className="mono">
            TEAM NEURALSHIFT · AI FOR BUSINESS & COMMERCE
          </span>
        </div>
        <Link href="/under-the-hood">See how it works ↗</Link>
      </footer>
    </>
  );
}
