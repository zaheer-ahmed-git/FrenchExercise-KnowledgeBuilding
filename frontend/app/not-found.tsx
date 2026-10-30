import Link from "next/link";
export default function NotFound() { return <section className="empty"><h1>Cette leçon n’existe pas.</h1><Link className="button" href="/">Retour au catalogue</Link></section>; }
