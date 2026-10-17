import fs from "node:fs";
import path from "node:path";
import Link from "next/link";
const tools = [
  [
    "Next.js + TypeScript + Tailwind",
    "The mobile-first studio, keyboard review tools, contact sheets and merchant ledger.",
  ],
  [
    "FastAPI + Python",
    "Validates uploads and coordinates typed provider adapters without keeping request state in a server instance.",
  ],
  [
    "SAM / local rembg",
    "Hosted foreground segmentation with optional local removal. Demo edge-color masks are labeled clearly.",
  ],
  [
    "Stable Diffusion / FLUX",
    "FLUX Kontext edits the image surroundings. Four local composite variants keep the offline rehearsal working.",
  ],
  [
    "Gemini Flash / GPT-4o",
    "Vision-to-JSON listing copy and faithful Hindi/Marathi variants. A schema rejects incomplete responses.",
  ],
  [
    "Tavily / SerpAPI",
    "Searches comparable Indian marketplace offers, extracts explicit INR prices and keeps source links.",
  ],
  [
    "Redis + RQ / BackgroundTasks",
    "Queues independent bulk jobs. If Redis is missing or unreachable, a visible local queue fallback takes over.",
  ],
  [
    "SSE + shared repository",
    "Streams measured stage snapshots and saves jobs/images/history on a shared volume.",
  ],
  [
    "Shopify GraphQL / WooCommerce REST",
    "Creates a hidden product draft after explicit approval, then returns its ID and admin link.",
  ],
];
export default function UnderTheHood() {
  const svg = fs
    .readFileSync(
      path.join(process.cwd(), "public", "architecture.svg"),
      "utf8",
    )
    .replace(/<\?xml[^>]*\?>/g, "")
    .replace(/<!DOCTYPE[^>]*>/g, "");
  return (
    <div className="page hood-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">THE WORKSHOP MANUAL / 06</p>
          <h1>
            No smoke.
            <br />
            <em>Just the workings.</em>
          </h1>
        </div>
        <div className="heading-note">
          <p>
            A practical stack of existing tools,
            <br />
            with your judgment at the end.
          </p>
          <Link className="button ink" href="/create">
            See it working ↗
          </Link>
        </div>
      </div>
      <section className="architecture-sheet">
        <div className="panel-heading">
          <h2>The route from photo to draft.</h2>
          <span className="mono">SYSTEM PLATE / 001</span>
        </div>
        <div
          className="architecture-scroll"
          role="img"
          aria-label="Architecture: merchant uses Next.js to send photos and approval to FastAPI. A Redis/RQ or local queue runs timed model and price adapters with labeled offline fallbacks and shared storage. SSE returns progress. Only explicit approval invokes Shopify or WooCommerce draft APIs."
          dangerouslySetInnerHTML={{ __html: svg }}
        />
        <p className="caption">
          Inline SVG / scroll inside the plate on a small screen. A live store
          call happens only across the approval boundary. Offline fallback never
          pretends to be a successful live call.
        </p>
      </section>
      <section className="tool-ledger">
        <div className="section-heading">
          <div>
            <p className="eyebrow">THE TOOLS ON OUR BENCH</p>
            <h2>Each one has a job.</h2>
          </div>
          <span className="badge">PROVIDERS ARE REPLACEABLE ADAPTERS</span>
        </div>
        {tools.map(([name, role], index) => (
          <article key={name}>
            <span className="mono">
              {(index + 1).toString().padStart(2, "0")}
            </span>
            <h3>{name}</h3>
            <p>{role}</p>
          </article>
        ))}
      </section>
      <section className="feasibility-notes">
        <div>
          <p className="eyebrow">WHY THIS CAN WORK NOW</p>
          <h2>
            A shopkeeper’s phone.
            <br />
            <em>Some very capable APIs.</em>
          </h2>
        </div>
        <div>
          <article>
            <h3>Feasible without special hardware.</h3>
            <p>
              The image and vision models are mature, API-accessible tools.
              Hosted services provide cloud GPUs; a merchant does not need a
              workstation. Review keeps product claims and final prices in human
              hands. Accounts, credits and model availability still matter.
            </p>
          </article>
          <article>
            <h3>A path from one shop to many.</h3>
            <p>
              Stateless FastAPI instances can scale horizontally behind a load
              balancer. RQ workers handle bulk catalog batches. This hackathon
              uses a shared filesystem; a multi-host deployment needs a shared
              database/object store, authentication and tenant isolation first.
            </p>
          </article>
          <article>
            <h3>Repeat less. Spend less.</h3>
            <p>
              Price lookups use a TTL cache and HTTP/model clients are reused.
              Background variants run concurrently. Queue concurrency, batching
              and lighter vision models offer further latency and cost
              reductions; live timings and fees must be measured.
            </p>
          </article>
          <article>
            <h3>The next shelf.</h3>
            <p>
              More marketplaces, broader multilingual SEO support, short product
              videos and reviewed dynamic repricing are roadmap work. English,
              Hindi and Marathi copy already work in this build.
            </p>
          </article>
        </div>
      </section>
      <div className="hood-footnote">
        <p className="eyebrow">AN HONEST REHEARSAL</p>
        <p>
          Offline mode uses real local image compositing, illustrative copy and
          example prices. It does not run SAM, FLUX or live market research.
          Every fallback is marked. Live-key paths have contract tests; your
          account configuration needs its own smoke test before use.
        </p>
        <Link className="text-button" href="/settings">
          Open connections & preferences ↗
        </Link>
      </div>
    </div>
  );
}
