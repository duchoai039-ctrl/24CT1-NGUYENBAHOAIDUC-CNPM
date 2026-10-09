import { useState } from 'react';

const links = ['Features', 'Drift AI', 'FAQ'];
const ease = 'cubic-bezier(0.77,0,0.175,1)';

export default function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <nav className="absolute top-6 left-1/2 -translate-x-1/2 z-50">
      <div className="flex items-center gap-10 bg-white rounded-full shadow-lg pl-6 pr-3 py-2">
        <span className="text-lg font-bold tracking-tight text-black">Drift.</span>
        <button
          id="nav-menu-toggle"
          type="button"
          aria-label={open ? 'Close menu' : 'Open menu'}
          aria-expanded={open}
          onClick={() => setOpen((o) => !o)}
          className="relative w-9 h-9 flex items-center justify-center rounded-full hover:bg-black/5 transition-colors"
        >
          <span
            className={`absolute h-[2px] w-5 bg-black rounded-full transition-transform duration-300 ${
              open ? 'translate-y-0 rotate-45' : '-translate-y-[4px]'
            }`}
            style={{ transitionTimingFunction: ease }}
          />
          <span
            className={`absolute h-[2px] w-5 bg-black rounded-full transition-transform duration-300 ${
              open ? 'translate-y-0 -rotate-45' : 'translate-y-[4px]'
            }`}
            style={{ transitionTimingFunction: ease }}
          />
        </button>
      </div>

      <div
        className={`absolute left-0 right-0 top-full mt-2 bg-white rounded-2xl shadow-lg p-2 origin-top transition-all duration-300 ${
          open
            ? 'opacity-100 scale-100 translate-y-0'
            : 'opacity-0 scale-95 -translate-y-2 pointer-events-none'
        }`}
        style={{ transitionTimingFunction: ease }}
      >
        {links.map((link) => (
          <a
            key={link}
            id={`nav-link-${link.toLowerCase().replace(/\s+/g, '-')}`}
            href={`#${link.toLowerCase().replace(/\s+/g, '-')}`}
            onClick={() => setOpen(false)}
            className="block px-4 py-2.5 text-sm font-medium text-black rounded-xl hover:bg-black/5 transition-colors"
          >
            {link}
          </a>
        ))}
      </div>
    </nav>
  );
}
