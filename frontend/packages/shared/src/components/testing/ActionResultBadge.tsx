import type { CommandOutcome, CommandSendMetadata } from "../../stores/useCombatStore";
import { classifyOutcome } from "../../testing/actionCatalog";

type ActionResultBadgeProps = {
  outcome: CommandOutcome | null;
  pending: CommandSendMetadata | null;
  requestId?: string;
};

export function ActionResultBadge({ outcome, pending, requestId }: ActionResultBadgeProps): JSX.Element {
  const status = pending ? "pending" : classifyOutcome(outcome);

  const statusClassName =
    status === "success"
      ? "bg-emerald-700/20 text-emerald-200 border-emerald-600/60"
      : status === "denied"
        ? "bg-amber-700/20 text-amber-200 border-amber-600/60"
        : status === "error"
          ? "bg-rose-700/20 text-rose-200 border-rose-600/60"
          : status === "pending"
            ? "bg-sky-700/20 text-sky-200 border-sky-600/60"
            : "bg-slate-700/30 text-slate-300 border-slate-600/50";

  const label = status === "success" ? "Success" : status === "denied" ? "Denied" : status === "error" ? "Error" : status === "pending" ? "Pending" : "No Result";

  const resolvedRequestId = requestId ?? pending?.requestId ?? outcome?.requestId;

  return (
    <div className={`rounded border px-3 py-2 text-xs ${statusClassName}`}>
      <div className="flex items-center justify-between gap-3">
        <span className="font-semibold uppercase tracking-wide">{label}</span>
        <span className="font-mono text-[11px]">request_id: {resolvedRequestId ?? "n/a"}</span>
      </div>

      {pending && <p className="mt-2 text-[11px]">Awaiting terminal event for {pending.sentType}.</p>}

      {!pending && outcome && (
        <div className="mt-2 space-y-1 text-[11px]">
          <p>
            sent: <span className="font-mono">{outcome.sentType}</span> {"->"} terminal: <span className="font-mono">{outcome.terminalType}</span>
          </p>
          {outcome.reasonCode && <p>reason: {outcome.reasonCode}</p>}
          {outcome.message && <p>message: {outcome.message}</p>}
          <p>at: {outcome.at}</p>
        </div>
      )}
    </div>
  );
}
