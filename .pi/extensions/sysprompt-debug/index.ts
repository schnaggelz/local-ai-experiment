import { writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import type {
  ExtensionAPI,
  BeforeAgentStartEvent,
  BeforeAgentStartEventResult,
} from "@earendil-works/pi-coding-agent";

const DUMP_FILE = join(resolve(process.env.HOME || ""), ".pi/sysprompt-dump.txt");

// Queue: when set to a non-empty string, the next before_agent_start will
// replace the system prompt with this value, then drain it.
let queuedSnapshot: string | undefined;

export default function (pi: ExtensionAPI) {
  // ---------------------------------------------------------------------------
  // /dump-sysprompt  —  dump current system prompt to file
  // ---------------------------------------------------------------------------
  pi.registerCommand("dump-sysprompt", {
    description: "Dump current system prompt to file and show stats",
    handler: async (_args, ctx) => {
      const sysPrompt = ctx.getSystemPrompt();

      try {
        writeFileSync(DUMP_FILE, sysPrompt);
        ctx.ui.notify(
          `system prompt written (${sysPrompt.length} chars, ${sysPrompt.split("\n").length} lines) -> ${DUMP_FILE}`,
          "info",
        );
        ctx.ui.setStatus("dump-sysprompt", `SP dump: ${sysPrompt.length} chars`);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        ctx.ui.notify(`Failed to write system prompt: ${msg}`, "error");
      }
    },
  });

  // ---------------------------------------------------------------------------
  // /repush-sysprompt — snapshot & queue one-shot re-inject for next call
  // ---------------------------------------------------------------------------
  pi.registerCommand("repush-sysprompt", {
    description:
      "Snapshot current system prompt and force-reinject it ONCE into the next agent call (auto-drains after firing).",
    handler: async (_args, ctx) => {
      queuedSnapshot = ctx.getSystemPrompt();

      ctx.ui.notify(
        `Re-push queued. Snapshot: ${queuedSnapshot.length} chars. Will inject on next agent call.`,
        "info",
      );
      ctx.ui.setStatus("repush-sysprompt", `🔁 queued (${queuedSnapshot.length})`);
    },
  });

  // ---------------------------------------------------------------------------
  // session_start — log on load
  // ---------------------------------------------------------------------------
  pi.on("session_start", (_event, ctx) => {
    const sysPrompt = ctx.getSystemPrompt();
    ctx.ui.notify(
      `sysprompt-debug extension loaded. System prompt: ${sysPrompt.length} chars / ${sysPrompt.split("\n").length} lines`,
      "info",
    );
  });

  // ---------------------------------------------------------------------------
  // before_agent_start — dump, and fire queued snapshot if any
  // ---------------------------------------------------------------------------
  pi.on(
    "before_agent_start",
    (event: BeforeAgentStartEvent, ctx): BeforeAgentStartEventResult | void => {
      // Always write dump of what Pi is about to send.
      try { writeFileSync(DUMP_FILE, event.systemPrompt); } catch { /* best-effort */ }

      if (!queuedSnapshot) return;

      const snapshot = queuedSnapshot!;
      queuedSnapshot = undefined; // drain immediately — one-shot only

      ctx.ui.notify(
        `Re-push FIRED: replacing ${event.systemPrompt.length} chars system prompt with ${snapshot.length} chars snapshot`,
        "info",
      );
      ctx.ui.setStatus("repush-sysprompt", "re-push fired ✓");

      return { systemPrompt: snapshot };
    },
  );
}
