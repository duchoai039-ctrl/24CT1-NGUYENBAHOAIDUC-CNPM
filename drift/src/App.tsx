import Navbar from './components/Navbar';
import AboutSection from './components/AboutSection';
import FeaturesSection from './components/FeaturesSection';

const HERO_VIDEO =
  'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260711_090308_1dd0cea7-f9ba-4db4-8147-c7d746061c9e.mp4';

export default function App() {
  return (
    <main>
      <section id="hero" className="relative h-screen overflow-hidden mb-[-25px]">
        <video
          src={HERO_VIDEO}
          autoPlay
          muted
          loop
          playsInline
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-black/20" />

        <Navbar />

        <div className="relative z-10 h-full flex flex-col justify-end items-center px-6 pb-12 md:pb-16">
          <div className="flex flex-col items-center gap-6 md:gap-8">
            <h1 className="text-center text-white font-normal leading-[1.1] tracking-tight text-5xl sm:text-7xl md:text-8xl lg:text-[96px]">
              <span className="block">Own your time</span>
              <span className="block">
                without{' '}
                <em
                  className="not-italic"
                  style={{ fontFamily: "'Instrument Serif', serif", fontStyle: 'italic' }}
                >
                  the stress
                </em>
              </span>
            </h1>

            <p className="text-white/80 text-sm md:text-base font-medium max-w-[420px] text-center">
              Drift is a calm, ADHD-friendly planner that turns scattered ideas into a clear path
            </p>

            <div className="bg-black/25 backdrop-blur-md rounded-xl flex flex-row items-center gap-4 pl-6 pr-1 py-1">
              <span className="hidden sm:inline text-white text-sm font-medium">
                No noise. No complicated systems. Just your day, gently sorted.
              </span>
              <span className="sm:hidden text-white text-sm font-medium">
                No noise. Just your day, gently sorted.
              </span>
              <button
                id="hero-cta"
                type="button"
                className="shrink-0 bg-white text-black text-sm font-medium px-5 py-2.5 rounded-xl hover:bg-white/90 transition-colors"
              >
                Start for free
              </button>
            </div>
          </div>
        </div>
      </section>

      <AboutSection />
      <FeaturesSection />
    </main>
  );
}
