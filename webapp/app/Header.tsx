import Link from "next/link";

export default function Header() {
  return (
    <header className="top">
      <div className="wrap">
        <span className="brand">WSQF-AI</span>
        <nav className="nav-links">
          <Link href="/">Product</Link>
          <Link href="/research">Research</Link>
          <a className="gh" href="https://github.com/SushilRaj0177/Project-KAGUTSUCHI">
            Source →
          </a>
        </nav>
      </div>
    </header>
  );
}
