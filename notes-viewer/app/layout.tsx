import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "GLO — Notes Archive",
  description: "Browse GLO's Substack notes by day, week, month or year.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="wrap">
          <header className="site">
            <h1>
              <Link href="/">GLO — Notes Archive</Link>
            </h1>
            <div className="sub">thepillarsofwisdom · substack-intelligence</div>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
