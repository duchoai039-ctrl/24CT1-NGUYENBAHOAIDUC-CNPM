import { useEffect, useRef, useState } from 'react';
import DriftLogo from './DriftLogo';

const BG_IMAGE =
  'https://images.higgs.ai/?default=1&output=webp&url=https%3A%2F%2Fd8j0ntlcm91z4.cloudfront.net%2Fuser_38xzZboKViGWJOttwIXH07lWA1P%2Fhf_20260709_082449_46df5cc4-ad98-4541-9236-a2659c1478a4.png&w=1920&q=85';

const features = [
  {
    title: 'Built for ease, not urgency',
    description:
      'Drift strips away the noise that makes organizing feel draining. Every surface is made to be soft, quiet, and intuitive so you can move forward, not get stuck decoding.',
    video:
      'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260702_102608_5fa1187d-9ac6-44fb-82ab-54376200abc0.mp4',
  },
  {
    title: 'The gentlest way to start',
    description:
      'Beginning your day should feel natural, not daunting. Drift eases you into motion with subtle cues and a quiet view of what deserves your energy right now.',
    video:
      'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260625_174131_395bc785-bb21-4e65-abf6-27c56f0764b6.mp4',
  },
  {
    title: 'Deep, undivided focus',
    description:
      'No interruptions, no clutter. Drift holds you in the present task with a stripped-back layout that softens all else until you are truly ready to shift.',
    video:
      'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260525_052706_d2e390fd-1846-4fe7-a4d8-8d2f1c875358.mp4',
  },
];

export default function FeaturesSection() {
  const [active, setActive] = useState(0);
  const [revealed, setRevealed] = useState<boolean[]>(() => features.map(() => false));
  const cardRefs = useRef<(HTMLElement | null)[]>([]);

  useEffect(() => {
    const cards = cardRefs.current.filter(Boolean) as HTMLElement[];

    const activeObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActive(Number((entry.target as HTMLElement).dataset.index));
          }
        });
      },
      { threshold: 0.6 },
    );

    const revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const idx = Number((entry.target as HTMLElement).dataset.index);
            setRevealed((prev) => {
              if (prev[idx]) return prev;
              const next = [...prev];
              next[idx] = true;
              return next;
            });
            revealObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15 },
    );

    cards.forEach((card) => {
      activeObserver.observe(card);
      revealObserver.observe(card);
    });

    return () => {
      activeObserver.disconnect();
      revealObserver.disconnect();
    };
  }, []);

  const scrollToCard = (i: number) => {
    cardRefs.current[i]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };

  return (
    <section id="features" className="relative px-5 md:px-10 lg:px-16 py-20 md:py-40 lg:py-48">
      {/* Fixed background image (clipped to this section) */}
      <div className="absolute inset-0 -z-10" style={{ clipPath: 'inset(0)' }}>
        <div
          className="fixed inset-0 bg-cover bg-center"
          style={{ backgroundImage: `url("${BG_IMAGE}")` }}
        />
      </div>

      <div className="lg:grid lg:grid-cols-[400px_1fr] xl:grid-cols-[460px_1fr] lg:gap-24 xl:gap-48">
        {/* Left column */}
        <div className="lg:sticky lg:top-0 lg:h-screen lg:flex lg:flex-col lg:justify-between lg:py-32 mb-12 lg:mb-0">
          <h2 className="text-white text-2xl sm:text-3xl lg:text-[46px] leading-[1.2] font-normal">
            Software that flows with your mind, not over it
          </h2>

          <div className="hidden lg:flex flex-col items-start gap-2">
            {features.map((f, i) => (
              <button
                key={f.title}
                id={`feature-nav-${i + 1}`}
                type="button"
                onClick={() => scrollToCard(i)}
                className={`bg-black/20 backdrop-blur-sm rounded-xl px-4 py-2.5 text-sm font-medium text-left transition-colors duration-300 ${
                  active === i ? 'text-white' : 'text-white/40 hover:text-white/70'
                }`}
              >
                {f.title}
              </button>
            ))}
          </div>

          <div className="hidden lg:flex flex-col items-start gap-4">
            <p className="text-white text-sm font-medium max-w-[300px]">
              No noise. No complicated systems. Just your day, gently sorted.
            </p>
            <button
              id="features-cta"
              type="button"
              className="bg-white text-black text-sm font-medium px-5 py-2.5 rounded-xl hover:bg-white/90 transition-colors"
            >
              Start for free
            </button>
          </div>
        </div>

        {/* Right column */}
        <div className="flex flex-col gap-8 md:gap-16 lg:py-32">
          {features.map((f, i) => (
            <article
              key={f.title}
              id={`feature-card-${i + 1}`}
              data-index={i}
              ref={(el) => {
                cardRefs.current[i] = el;
              }}
              className={`bg-black/20 backdrop-blur-sm rounded-3xl p-6 md:p-10 flex flex-col gap-6 transition-all duration-700 ease-out ${
                revealed[i] ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-16'
              }`}
            >
              <DriftLogo fill="rgba(255,255,255,0.8)" />
              <h3 className="text-white text-xl md:text-2xl font-medium">{f.title}</h3>
              <div className="aspect-video rounded-2xl overflow-hidden bg-black/30">
                <video
                  src={f.video}
                  autoPlay
                  muted
                  loop
                  playsInline
                  className="w-full h-full object-cover"
                />
              </div>
              <p className="text-white/60 font-medium text-sm md:text-base leading-relaxed">
                {f.description}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
