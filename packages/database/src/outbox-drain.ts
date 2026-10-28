import { eq, and, lte, sql } from "drizzle-orm";
import { db } from "./index";
import { taskOutbox, type TaskOutboxRecord } from "./schema";

export interface EnqueueTaskInput {
  type: string;
  dedupeKey?: string | null;
  payload?: Record<string, unknown>;
  scheduledFor?: Date;
}

export interface TaskCompletion {
  kind: "terminal" | "retry";
  status: "done" | "skipped" | "failed";
  attempts: number;
  lastError?: string | null;
  scheduledFor?: Date;
}

/**
 * Inserts a task idempotently into task_outbox.
 * Skips duplicates if (type, dedupeKey) already exists without aborting transaction.
 */
export async function insertTask(input: EnqueueTaskInput): Promise<{ created: boolean; id?: string }> {
  const result = await db
    .insert(taskOutbox)
    .values({
      type: input.type,
      dedupeKey: input.dedupeKey ?? null,
      payload: input.payload ?? {},
      scheduledFor: input.scheduledFor ?? new Date(),
    })
    .onConflictDoNothing({ target: [taskOutbox.type, taskOutbox.dedupeKey] })
    .returning({ id: taskOutbox.id });

  if (result.length > 0) {
    return { created: true, id: result[0].id };
  }

  // Already exists
  return { created: false };
}

/**
 * Claims a pending task atomically with a unique processingToken.
 * Prevents concurrent workers from executing the same job.
 */
export async function claimTask(id: string, now = new Date()): Promise<string | null> {
  const processingToken = crypto.randomUUID();

  const result = await db
    .update(taskOutbox)
    .set({
      status: "processing",
      processingToken,
      updatedAt: now,
    })
    .where(
      and(
        eq(taskOutbox.id, id),
        eq(taskOutbox.status, "pending"),
        lte(taskOutbox.scheduledFor, now)
      )
    )
    .returning({ id: taskOutbox.id });

  return result.length === 1 ? processingToken : null;
}

/**
 * Completes a task atomically.
 * If terminal, redacts the payload to {} to comply with data protection and reduce storage.
 */
export async function completeTask(
  id: string,
  processingToken: string,
  completion: TaskCompletion,
  now = new Date()
): Promise<boolean> {
  const updateData =
    completion.kind === "terminal"
      ? {
          status: completion.status,
          attempts: completion.attempts,
          lastError: completion.lastError ?? null,
          payload: {}, // Redacted on completion
          processedAt: now,
          redactedAt: now,
          processingToken: null,
          updatedAt: now,
        }
      : {
          status: "pending",
          attempts: completion.attempts,
          lastError: completion.lastError ?? null,
          scheduledFor: completion.scheduledFor ?? now,
          processingToken: null,
          updatedAt: now,
        };

  const result = await db
    .update(taskOutbox)
    .set(updateData)
    .where(
      and(
        eq(taskOutbox.id, id),
        eq(taskOutbox.processingToken, processingToken),
        eq(taskOutbox.status, "processing")
      )
    )
    .returning({ id: taskOutbox.id });

  return result.length === 1;
}

/**
 * Recovers tasks stuck in 'processing' status past lease duration (e.g. 5 minutes).
 */
export async function recoverStaleLeases(leaseTimeoutMs = 300_000, now = new Date()): Promise<number> {
  const staleThreshold = new Date(now.getTime() - leaseTimeoutMs);

  const result = await db
    .update(taskOutbox)
    .set({
      status: "pending",
      processingToken: null,
      updatedAt: now,
    })
    .where(
      and(
        eq(taskOutbox.status, "processing"),
        lte(taskOutbox.updatedAt, staleThreshold)
      )
    )
    .returning({ id: taskOutbox.id });

  return result.length;
}

/**
 * Fetches pending tasks ready for processing.
 */
export async function fetchPendingTasks(limit = 10, now = new Date()): Promise<TaskOutboxRecord[]> {
  return db
    .select()
    .from(taskOutbox)
    .where(
      and(
        eq(taskOutbox.status, "pending"),
        lte(taskOutbox.scheduledFor, now)
      )
    )
    .limit(limit);
}

export type TaskHandler = (task: TaskOutboxRecord) => Promise<{ success: boolean; error?: string }>;

export interface DrainOptions {
  batchSize?: number;
  maxAttempts?: number;
  baseBackoffMs?: number;
  handlers: Record<string, TaskHandler>;
}

/**
 * Robust outbox drain cycle:
 * Claims pending tasks, dispatches them to matching handlers, and completes or reschedules
 * with exponential backoff without crashing the application.
 */
export async function drainTaskOutbox(options: DrainOptions): Promise<{ processed: number; succeeded: number; failed: number }> {
  const batchSize = options.batchSize ?? 10;
  const maxAttempts = options.maxAttempts ?? 5;
  const baseBackoffMs = options.baseBackoffMs ?? 5_000;

  // 1. Recover stale leases first (e.g. crashed workers)
  await recoverStaleLeases();

  // 2. Fetch batch of ready tasks
  const tasks = await fetchPendingTasks(batchSize);
  let succeeded = 0;
  let failed = 0;

  for (const task of tasks) {
    const token = await claimTask(task.id);
    if (!token) continue; // Claimed by concurrent worker

    const handler = options.handlers[task.type];
    if (!handler) {
      // Unknown task type: mark as skipped
      await completeTask(task.id, token, {
        kind: "terminal",
        status: "skipped",
        attempts: task.attempts + 1,
        lastError: `No handler registered for task type: ${task.type}`,
      });
      failed++;
      continue;
    }

    try {
      const result = await handler(task);
      if (result.success) {
        await completeTask(task.id, token, {
          kind: "terminal",
          status: "done",
          attempts: task.attempts + 1,
        });
        succeeded++;
      } else {
        const nextAttempts = task.attempts + 1;
        if (nextAttempts >= maxAttempts) {
          await completeTask(task.id, token, {
            kind: "terminal",
            status: "failed",
            attempts: nextAttempts,
            lastError: result.error ?? "Max attempts reached",
          });
          failed++;
        } else {
          const backoffDelay = baseBackoffMs * Math.pow(2, task.attempts);
          const nextRun = new Date(Date.now() + backoffDelay);
          await completeTask(task.id, token, {
            kind: "retry",
            status: "failed",
            attempts: nextAttempts,
            lastError: result.error ?? "Handler returned failure",
            scheduledFor: nextRun,
          });
          failed++;
        }
      }
    } catch (err: any) {
      const nextAttempts = task.attempts + 1;
      const errorMsg = err?.message || String(err);
      if (nextAttempts >= maxAttempts) {
        await completeTask(task.id, token, {
          kind: "terminal",
          status: "failed",
          attempts: nextAttempts,
          lastError: `Unhandled exception: ${errorMsg}`,
        });
        failed++;
      } else {
        const backoffDelay = baseBackoffMs * Math.pow(2, task.attempts);
        const nextRun = new Date(Date.now() + backoffDelay);
        await completeTask(task.id, token, {
          kind: "retry",
          status: "failed",
          attempts: nextAttempts,
          lastError: `Unhandled exception: ${errorMsg}`,
          scheduledFor: nextRun,
        });
        failed++;
      }
    }
  }

  return { processed: tasks.length, succeeded, failed };
}

