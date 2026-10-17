"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { api, Channel, Job, money, seconds } from "@/lib/api";
import { useLedger, statusLabel } from "@/lib/useLedger";
export default function Bulk() {
  const { jobs, loading, error: loadError, refresh } = useLedger();
  const [files, setFiles] = useState<File[]>([]),
    [ids, setIds] = useState<string[]>([]),
    [selected, setSelected] = useState<Record<string, number>>({}),
    [approved, setApproved] = useState(false),
    [channel, setChannel] = useState<Channel>("shopify");
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    try {
      setIds(JSON.parse(localStorage.getItem("s2s.bulk.ids") || "[]"));
    } catch {}
  }, []);
  function remember(next: string[]) {
    setIds(next);
    localStorage.setItem("s2s.bulk.ids", JSON.stringify(next));
  }
  function choose(chosen: File[]) {
    setError("");
    if (chosen.length < 1 || chosen.length > 20) {
      setError(
        "Choose 1–20 product photos per batch. Each photo becomes one listing.",
      );
      return;
    }
    if (
      chosen.some(
        (file) =>
          !["image/jpeg", "image/png", "image/webp"].includes(file.type) ||
          file.size > 10 * 1024 * 1024,
      )
    ) {
      setError("Every file must be JPG, PNG or WebP and at most 10 MB.");
      return;
    }
    setFiles(chosen);
  }
  async function start() {
    setBusy(true);
    setError("");
    setSelected({});
    setApproved(false);
    const next: string[] = [];
    try {
      for (const file of files) {
        const body = new FormData();
        body.append("files", file);
        const job = await api<Job>("/jobs", { method: "POST", body });
        next.push(job.id);
        remember([...next]);
      }
      setFiles([]);
      setNotice(
        `${next.length} products accepted. Each gets its own job and review.`,
      );
      await refresh();
    } catch (reason) {
      setError(
        (reason as Error).message + " Accepted jobs remain in the queue below.",
      );
    } finally {
      setBusy(false);
    }
  }
  function select(job: Job, checked: boolean) {
    setSelected((previous) => {
      const next = { ...previous };
      if (checked) next[job.id] = job.revision;
      else delete next[job.id];
      return next;
    });
    setApproved(false);
  }
  async function publish(idsToPublish: string[]) {
    setBusy(true);
    setError("");
    let count = 0;
    try {
      for (const id of idsToPublish) {
        await api<Job>("/jobs/" + id + "/publish", {
          method: "POST",
          body: JSON.stringify({
            channel,
            approved: true,
            revision: selected[id],
          }),
        });
        count++;
        setSelected((previous) => {
          const next = { ...previous };
          delete next[id];
          return next;
        });
      }
      setNotice(
        `${count} approved drafts processed. Each receipt says whether it stayed local or reached a live store.`,
      );
    } catch (reason) {
      setError(
        (reason as Error).message +
          ` ${count} drafts were processed before this error.`,
      );
    } finally {
      setApproved(false);
      setBusy(false);
      refresh();
    }
  }
  const batch = ids
    .map((id) => jobs.find((job) => job.id === id))
    .filter((job): job is Job => Boolean(job));
  return (
    <div className="page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">THE BULK DESK / 02</p>
          <h1>
            A whole shelf.
            <br />
            <em>One contact sheet.</em>
          </h1>
        </div>
        <div className="heading-note">
          <p>
            One photo per product. Up to twenty products.
            <br />
            Review each draft before it leaves the desk.
          </p>
          <span className="badge">REDIS / RQ · LOCAL QUEUE FALLBACK</span>
        </div>
      </div>
      {(error || loadError) && (
        <div className="message error" role="alert">
          {error || loadError}
          <button className="text-button" onClick={refresh}>
            Refresh queue ↻
          </button>
        </div>
      )}
      {notice && (
        <div className="message" role="status">
          {notice}
        </div>
      )}
      <div
        className="batch-ingest"
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          if (!busy) choose(Array.from(event.dataTransfer.files));
        }}
      >
        <div>
          <p className="eyebrow">MULTIPLE PRODUCTS / SINGLE-FRAME MODE</p>
          <h2>
            {files.length
              ? `${files.length} photos on the desk.`
              : "Drop a batch. Keep your afternoon."}
          </h2>
          <p>
            JPG, PNG or WebP. 10 MB each. Need several angles of one product?
            Use <Link href="/create">the studio</Link>.
          </p>
        </div>
        <div className="button-row">
          <button
            className="button outline"
            onClick={() => input.current?.click()}
            disabled={busy}
          >
            Choose batch ↑
          </button>
          <button
            className="button accent"
            onClick={start}
            disabled={busy || !files.length}
          >
            {busy
              ? "Working through the batch…"
              : `Develop ${files.length || ""} ${files.length === 1 ? "product" : "products"}`}{" "}
            ↗
          </button>
        </div>
        <input
          className="sr-only"
          ref={input}
          data-testid="batch-input"
          type="file"
          multiple
          accept="image/jpeg,image/png,image/webp"
          onChange={(event) => choose(Array.from(event.target.files || []))}
          aria-label="Batch product photos"
        />
      </div>
      {files.length > 0 && (
        <ul className="file-manifest">
          {files.map((file, index) => (
            <li key={index}>
              <span className="mono">
                {(index + 1).toString().padStart(2, "0")}
              </span>
              {file.name}
              <small>{(file.size / 1024).toFixed(0)} KB</small>
            </li>
          ))}
        </ul>
      )}
      <div className="section-divider">
        <span className="eyebrow">CURRENT BATCH / {batch.length} PRODUCTS</span>
        <button
          className="text-button"
          onClick={() => {
            remember([]);
            setSelected({});
            setApproved(false);
          }}
          disabled={busy}
        >
          Clear this desk{" "}
          <span className="caption">(records stay in your ledger)</span>
        </button>
      </div>
      {loading ? (
        <p className="message" role="status">
          Checking the job queue…
        </p>
      ) : batch.length === 0 ? (
        <div className="empty-panel">
          <span className="mono">00 / AWAITING A CONTACT SHEET</span>
          <h2>Room for your next collection.</h2>
          <p>
            Choose a few product photos above. Their processing status and draft
            review links will appear here.
          </p>
        </div>
      ) : (
        <>
          <div className="batch-grid">
            {batch.map((job, index) => (
              <article className="batch-card" key={job.id}>
                <div className="batch-image">
                  <img
                    src={
                      job.result?.variants[job.result.selected_style] ||
                      job.source_images[0]
                    }
                    alt={
                      job.result?.copy.title || "Batch product " + (index + 1)
                    }
                  />
                  <span className="sample-number">
                    {(index + 1).toString().padStart(2, "0")}
                  </span>
                  <span className={"status-tag " + job.status}>
                    {statusLabel(job)}
                  </span>
                </div>
                <div className="batch-details">
                  <h2>
                    {job.result?.copy.title || "Developing this product…"}
                  </h2>
                  <p className="caption">
                    {
                      job.stages.filter((stage) => stage.status === "completed")
                        .length
                    }
                    /6 stages · {seconds(job.elapsed_ms)} ·{" "}
                    {job.queue === "redis" ? "Redis/RQ" : "Local queue"}
                  </p>
                  {job.demo_data && (
                    <span className="badge">CONTAINS DEMO DATA</span>
                  )}
                  {job.error && <p className="caption">{job.error}</p>}
                  <div className="batch-card-actions">
                    <Link
                      className="text-button"
                      href={"/create?job=" + job.id}
                    >
                      {job.status === "published"
                        ? "Open receipt"
                        : "Review & edit"}{" "}
                      ↗
                    </Link>
                    {job.result && (
                      <strong>{money(job.result.final_price)}</strong>
                    )}
                  </div>
                  {job.status === "ready" && (
                    <>
                      <label className="approval-check">
                        <input
                          type="checkbox"
                          aria-label={
                            "Reviewed " + job.result?.copy.title + " " + job.id
                          }
                          checked={Boolean(selected[job.id])}
                          onChange={(event) =>
                            select(job, event.target.checked)
                          }
                          disabled={busy}
                        />
                        <span>I reviewed this photo, copy and price.</span>
                      </label>
                      <button
                        className="button outline full"
                        disabled={!selected[job.id] || busy}
                        onClick={() => publish([job.id])}
                      >
                        Approve this draft ↗
                      </button>
                    </>
                  )}
                  {job.store_result && (
                    <p className="caption">{job.store_result.message}</p>
                  )}
                </div>
              </article>
            ))}
          </div>
          <div className="batch-approval">
            <div>
              <p className="eyebrow">APPROVE THE CONTACT SHEET</p>
              <h2>{Object.keys(selected).length} reviewed drafts.</h2>
              <p>
                Only checked listings are included. Live destinations require
                credentials and a successful connection.
              </p>
            </div>
            <div>
              <label htmlFor="batch-store">Destination</label>
              <select
                id="batch-store"
                value={channel}
                onChange={(event) => {
                  setChannel(event.target.value as Channel);
                  setApproved(false);
                }}
              >
                <option value="shopify">Shopify</option>
                <option value="woocommerce">WooCommerce</option>
              </select>
              <label className="approval-check">
                <input
                  type="checkbox"
                  checked={approved}
                  onChange={(event) => setApproved(event.target.checked)}
                  disabled={!Object.keys(selected).length || busy}
                />
                <span>
                  I approve creating all selected <strong>drafts</strong> in
                  this destination.
                </span>
              </label>
              <button
                className="button accent full"
                onClick={() => publish(Object.keys(selected))}
                disabled={!approved || busy || !Object.keys(selected).length}
              >
                {busy
                  ? "Processing approved drafts…"
                  : "Approve selected drafts"}{" "}
                ↗
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
