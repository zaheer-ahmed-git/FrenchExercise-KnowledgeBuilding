import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Écouter l’IA en français",
  description: "Des leçons d’écoute sur l’actualité de l’intelligence artificielle.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="fr"><body><header className="site-header"><Link href="/" className="brand">écouter<span>IA</span></Link><p>Pratiquez votre français avec l’actualité de l’IA.</p></header><main>{children}</main><footer>Écouter IA · Leçons B1–B2</footer></body></html>;
}
