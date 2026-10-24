import { Activity } from "lucide-react";

import { CheckerStrip, StarBurst } from "@/components/nb/motifs";
import { NbMarquee } from "@/components/nb/marquee";
import { NbSticker } from "@/components/nb/sticker";

export function LoginArt() {
  return (
    <section className="login-visual nb-login-art" aria-labelledby="login-art-title">
      <div className="login-brand">
        <div className="brand-mark">A<span>G</span></div>
        <div>
          <b>APEXGRID</b>
          <small>RACE OPERATIONS</small>
        </div>
      </div>

      <div className="nb-login-art-body">
        <div className="nb-login-display-stack" id="login-art-title">
          <span className="nb-login-display">APEXGRID</span>
          <span aria-hidden="true" className="nb-login-display nb-login-display-stroke">APEXGRID</span>
        </div>
        <div className="visual-copy">
          <div className="eyebrow">
            <Activity aria-hidden="true" size={20} /> MOTORSPORT CONTROL SYSTEM
          </div>
          <p className="nb-login-hero-copy">
            Every lap.
            <br />
            <span>Under control.</span>
          </p>
          <p>Race weekend operations, championship data, and live telemetry in one place.</p>
        </div>
        <div className="nb-login-art-row">
          <NbSticker decorative className="nb-login-sticker" tone="yellow" tilt={-2}>
            <StarBurst points={8} className="nb-login-sticker-icon" />
            DBMS EDITION
          </NbSticker>
          <NbMarquee
            className="nb-login-marquee"
            items={["RACE CONTROL", "TELEMETRY", "STEWARDS", "PIT WALL", "STANDINGS"]}
            tone="red"
          />
        </div>
      </div>

      <div className="visual-footer">
        <span>RACE CONTROL PLATFORM</span>
        <span>01 — 06</span>
      </div>
      <CheckerStrip aria-hidden="true" className="nb-login-checker" />
      <span aria-hidden="true" className="tx-grid nb-login-art-texture" />
    </section>
  );
}
