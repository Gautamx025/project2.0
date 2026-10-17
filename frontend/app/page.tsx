import Link from "next/link";
import ImpactCalculator from "@/components/ImpactCalculator";
const steps = [
  [
    "Bring a photo",
    "One to three phone photos. A file picker, a drop, or your camera.",
  ],
  [
    "Find the product",
    "SAM isolates the foreground. Local fallbacks are always labeled.",
  ],
  [
    "Set the scene",
    "FLUX develops studio and lifestyle backgrounds, in four styles.",
  ],
  [
    "Find the words",
    "A vision model writes copy in English, Hindi and Marathi. You can edit it all.",
  ],
  [
    "Check the market",
    "Comparable INR offers anchor a price range. You choose the final price.",
  ],
  [
    "Approve the draft",
    "Review the payload, then approve a Shopify or WooCommerce draft.",
  ],
];
export default function Page() {
  return (
    <div className="page landing-page">
      <section className="landing-hero">
        <div className="hero-story">
          <p className="eyebrow">LESS CATALOG WORK. MORE SHOP TIME.</p>
          <h1>
            Good product.
            <br />
            Meet your
            <br />
            <em>good side.</em>
          </h1>
          <p className="hero-deck">
            From a photo on your shop counter to a listing worth putting in the
            window.
          </p>
          <p className="hero-body">
            Studio visuals, useful copy, a researched price. Snap-2-Store does
            the groundwork. You make the final call.
          </p>
          <div className="hero-actions">
            <Link href="/create" className="button accent">
              Try the working studio <span>↗</span>
            </Link>
            <Link href="/bulk" className="text-button">
              Or bring a whole shelf →
            </Link>
          </div>
          <p className="caption">
            No keys needed for the offline demo.
            <br />
            Nothing reaches a store without your approval.
          </p>
          <div className="hero-footnote">
            <span className="mono">BUILT FOR</span>
            <p>
              The corner shop. The local maker.
              <br />
              The brand doing it all themselves.
            </p>
          </div>
        </div>
        <div className="contact-composition">
          <div className="contact-title">
            <span>CONTACT SHEET / VOL. 001</span>
            <span>3 FRAMES. ENDLESS POTENTIAL.</span>
          </div>
          <div className="hero-contact">
            <figure className="contact-main">
              <div className="contact-photo">
                <img
                  src="/samples/bottle.jpg"
                  alt="White steel water bottle photographed on a shop-like tabletop with flowers"
                  fetchPriority="high"
                />
                <span className="frame-tag">01 / DRINKWARE</span>
              </div>
              <figcaption>
                <span>THE EVERYDAY ESSENTIAL</span>
                <strong>
                  One bottle.
                  <br />A better introduction.
                </strong>
              </figcaption>
            </figure>
            <figure className="contact-small">
              <div className="contact-photo">
                <img
                  src="/samples/watch.jpg"
                  alt="White digital watch on a pale background"
                />
                <span className="frame-tag">02</span>
              </div>
              <figcaption>TIME, WELL SPENT.</figcaption>
            </figure>
            <figure className="contact-small">
              <div className="contact-photo">
                <img
                  src="/samples/bag.jpg"
                  alt="Brown backpack with a zippered front pocket"
                />
                <span className="frame-tag">03</span>
              </div>
              <figcaption>READY TO GO PLACES.</figcaption>
            </figure>
          </div>
          <div className="contact-receipt">
            <span className="receipt-mark">s2s</span>
            <div>
              <span className="mono">THE RAW MATERIAL IS ALREADY GOOD.</span>
              <p>Let’s give it the catalog it deserves.</p>
            </div>
            <span className="receipt-arrow">↗</span>
          </div>
          <p className="caption">
            Bundled sample photographs. Illustrative inputs, not live AI
            results.
          </p>
        </div>
      </section>
      <section className="problem-spread">
        <div className="problem-number">
          <span className="eyebrow">THE SMALL-SELLER TAX</span>
          <strong>
            25–40<span>minutes</span>
          </strong>
          <p>
            Photography. Editing. Copy. Price checks.
            <br />
            For every single product.
          </p>
        </div>
        <div className="problem-copy">
          <p className="eyebrow">YOUR AFTERNOON HAS BETTER THINGS TO DO.</p>
          <h2>
            You opened a shop.
            <br />
            <em>Not a photo studio.</em>
          </h2>
          <p>
            A new shipment should mean new sales, not another evening of
            cropping photos and staring at an empty description box.
          </p>
          <p>
            Our aim: a reviewable product draft in under 30 seconds. The
            stopwatch measures every run honestly. Live providers may take
            longer; the demo never hides its local fallbacks.
          </p>
          <Link className="text-button" href="/under-the-hood">
            See what happens between photo and draft ↗
          </Link>
        </div>
      </section>
      <section className="how-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">FROM COUNTER TO CATALOG</p>
            <h2>
              Six careful steps.
              <br />
              <em>One less thing on your list.</em>
            </h2>
          </div>
          <span className="mono">AUTOMATIC UNTIL IT NEEDS YOUR SAY-SO.</span>
        </div>
        <ol className="how-steps">
          {steps.map(([title, description], index) => (
            <li key={title}>
              <span className="step-no">0{index + 1}</span>
              <h3>{title}</h3>
              <p>{description}</p>
            </li>
          ))}
        </ol>
      </section>
      <section className="projection-spread">
        <div className="projection-intro">
          <p className="eyebrow">WHAT BETTER CATALOG WORK COULD MEAN</p>
          <h2>
            Small changes.
            <br />
            <em>A fuller shop.</em>
          </h2>
          <span className="badge">
            PROJECTED FIGURES / NOT MEASURED RESULTS
          </span>
        </div>
        <div className="projection-ledger">
          <div>
            <strong>
              98<span>%</span>
            </strong>
            <h3>less preparation time</h3>
            <p>
              Modeled from the 25–40 minute baseline to our under-30-second
              processing goal. Review time is extra.
            </p>
          </div>
          <div>
            <strong>
              90<span>%</span>
            </strong>
            <h3>lower creation costs</h3>
            <p>
              A scenario with less photography gear, editing and copywriting
              work. API, hosting and store fees still apply.
            </p>
          </div>
          <div>
            <strong>
              +15–25<span>%</span>
            </strong>
            <h3>higher conversion potential</h3>
            <p>
              A projected lift from clearer visuals and useful SEO copy. This
              has not been validated in merchant trials.
            </p>
          </div>
        </div>
      </section>
      <ImpactCalculator compact />
      <section className="seller-notes">
        <div>
          <p className="eyebrow">FOR THE PEOPLE BEHIND THE COUNTER</p>
          <h2>
            A little more help.
            <br />
            <em>A lot more control.</em>
          </h2>
        </div>
        <div>
          <article>
            <span className="mono">01 / SMALL RETAILERS</span>
            <p>
              Put the new delivery online while the shop is still open. A phone
              and a product are enough to start.
            </p>
          </article>
          <article>
            <span className="mono">02 / LOCAL MAKERS</span>
            <p>
              Give each piece a consistent setting and a clear description, in
              the language your customers use.
            </p>
          </article>
          <article>
            <span className="mono">03 / D2C TEAMS</span>
            <p>
              Work through a whole collection at the bulk desk. Keep the final
              review with someone who knows the product.
            </p>
          </article>
        </div>
      </section>
      <section className="closing-note">
        <span className="eyebrow">TAKE ONE PHOTO. SEE WHAT DEVELOPS.</span>
        <h2>
          Faster, cheaper, better-looking catalogs without a studio or a
          copywriter.
        </h2>
        <Link href="/create" className="button accent">
          Make your first listing <span>↗</span>
        </Link>
        <p className="caption">
          Team NeuralShift / AI for Business and Commerce
        </p>
      </section>
    </div>
  );
}
