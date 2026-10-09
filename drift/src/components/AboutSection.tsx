import { Mail, Plus } from 'lucide-react';
import DriftLogo from './DriftLogo';

export default function AboutSection() {
  return (
    <section
      id="about"
      className="relative z-10 bg-[#F6E4CF] rounded-t-[25px] py-20 md:py-32 px-6"
    >
      {/* Top area */}
      <div className="max-w-3xl mx-auto flex flex-col items-center gap-8">
        <p className="text-[#321C04] text-base md:text-lg text-center leading-relaxed max-w-lg">
          We craft tools that move with your rhythm, not over it. Designed for ease, presence, and
          flow.
        </p>
        <div className="flex flex-wrap justify-center gap-4">
          <a
            id="about-say-hello"
            href="#"
            className="flex items-center gap-3 bg-[#321C04] text-[#FFF9F2] rounded-full pl-1.5 pr-6 py-1.5 text-sm uppercase tracking-wide font-medium hover:bg-[#1F1003] transition-colors"
          >
            <span className="w-9 h-9 rounded-full bg-[#FFF9F2] flex items-center justify-center text-[#321C04]">
              <Mail size={16} />
            </span>
            Say hello
          </a>
          <a
            id="about-stay-informed"
            href="#"
            className="flex items-center gap-3 bg-[#D9C4AA] text-[#321C04] rounded-full pl-1.5 pr-6 py-1.5 text-sm uppercase tracking-wide font-medium hover:bg-[#CEBA9E] transition-colors"
          >
            <span className="w-9 h-9 rounded-full bg-[#FFF9F2] flex items-center justify-center text-[#321C04]">
              <Plus size={16} />
            </span>
            Stay informed
          </a>
        </div>
      </div>

      {/* Divider */}
      <div className="max-w-6xl mx-auto flex items-center gap-[2px] my-16 md:my-24">
        <span className="w-2 h-2 rounded-full bg-[#D9C4AA]" />
        <span className="flex-1 h-[2px] bg-[#D9C4AA]" />
        <span className="w-2 h-2 rounded-full bg-[#D9C4AA]" />
      </div>

      {/* Bottom area */}
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row gap-10 md:gap-20">
        <div className="flex items-center md:items-start gap-4 shrink-0">
          <DriftLogo fill="#321C04" />
          <span className="text-xs uppercase tracking-widest font-semibold text-[#321C04] leading-tight">
            Calm
            <br />
            Amplified
          </span>
        </div>
        <p className="text-2xl sm:text-3xl md:text-4xl lg:text-[42px] leading-[1.3] font-normal text-[#321C04]">
          We make AI tools and assistants. But, most importantly, we help you remember what gentle
          productivity looks like when software moves with you, not over you. We create systems
          that carry the cognitive weight, so you can attend to what truly counts.
        </p>
      </div>
    </section>
  );
}
