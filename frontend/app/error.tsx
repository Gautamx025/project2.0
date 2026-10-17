"use client";
export default function Error({ reset }: { reset: () => void }) {
  return (
    <div className="page empty-state" role="alert">
      <p className="eyebrow">A FRAME OUT OF PLACE</p>
      <h1>This page couldn’t develop.</h1>
      <p>
        Your saved jobs are still in the ledger. Try loading the page again.
      </p>
      <button className="button accent" onClick={reset}>
        Try again ↻
      </button>
    </div>
  );
}
