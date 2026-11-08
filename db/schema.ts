import {
  boolean,
  int,
  json,
  mysqlEnum,
  mysqlTable,
  serial,
  text,
  timestamp,
  varchar,
} from "drizzle-orm/mysql-core";

export const debates = mysqlTable("debates", {
  id: varchar("id", { length: 64 }).primaryKey(),
  title: varchar("title", { length: 255 }).notNull(),
  question: text("question").notNull(),
  summary: text("summary").notNull(),
  sourceName: varchar("source_name", { length: 255 }).notNull(),
  sourceUrl: text("source_url").notNull(),
  methodNote: text("method_note").notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const evidence = mysqlTable("evidence", {
  id: varchar("id", { length: 64 }).primaryKey(),
  debateId: varchar("debate_id", { length: 64 }).notNull(),
  title: varchar("title", { length: 255 }).notNull(),
  authors: text("authors").notNull(),
  publisher: varchar("publisher", { length: 255 }).notNull(),
  publishedAt: varchar("published_at", { length: 64 }).notNull(),
  url: text("url").notNull(),
  sourceType: mysqlEnum("source_type", [
    "peer_reviewed",
    "advocacy_report",
    "government_report",
    "news_analysis",
    "debate_collection",
  ]).notNull(),
  excerpt: text("excerpt").notNull(),
  finding: text("finding").notNull(),
  limitation: text("limitation").notNull(),
  reviewStatus: mysqlEnum("review_status", ["reviewed", "unreviewed", "disputed"])
    .default("reviewed")
    .notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const statements = mysqlTable("statements", {
  id: varchar("id", { length: 64 }).primaryKey(),
  debateId: varchar("debate_id", { length: 64 }).notNull(),
  owner: mysqlEnum("owner", ["shared", "advocate", "critic"]).notNull(),
  kind: mysqlEnum("kind", [
    "definition",
    "empirical",
    "normative",
    "design",
    "bridge",
    "conclusion",
  ]).notNull(),
  title: varchar("title", { length: 255 }).notNull(),
  body: text("body").notNull(),
  formalText: text("formal_text").notNull(),
  formalizationNote: text("formalization_note").notNull(),
  evidenceId: varchar("evidence_id", { length: 64 }),
  sortOrder: int("sort_order").notNull(),
  isWorkshop: boolean("is_workshop").default(false).notNull(),
  approvalStatus: mysqlEnum("approval_status", ["approved", "disputed", "draft"])
    .default("approved")
    .notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
});

export const proofs = mysqlTable("proofs", {
  id: varchar("id", { length: 64 }).primaryKey(),
  debateId: varchar("debate_id", { length: 64 }).notNull(),
  theoremName: varchar("theorem_name", { length: 128 }).notNull(),
  title: varchar("title", { length: 255 }).notNull(),
  conclusionId: varchar("conclusion_id", { length: 64 }).notNull(),
  owner: mysqlEnum("owner", ["shared", "advocate", "critic"]).notNull(),
  description: text("description").notNull(),
  premiseIds: json("premise_ids").$type<string[]>().notNull(),
  leanCode: text("lean_code").notNull(),
  status: mysqlEnum("status", ["verified", "failed", "unverified", "unavailable"])
    .default("unverified")
    .notNull(),
  verifierOutput: text("verifier_output"),
  axiomReport: text("axiom_report"),
  proofHash: varchar("proof_hash", { length: 64 }),
  toolchain: varchar("toolchain", { length: 64 }),
  verifiedAt: timestamp("verified_at"),
  isNegativeControl: boolean("is_negative_control").default(false).notNull(),
});

export const verificationRuns = mysqlTable("verification_runs", {
  id: serial("id").primaryKey(),
  proofId: varchar("proof_id", { length: 64 }).notNull(),
  sourceHash: varchar("source_hash", { length: 64 }).notNull(),
  outcome: mysqlEnum("outcome", ["accepted", "rejected", "unavailable"]).notNull(),
  output: text("output").notNull(),
  toolchain: varchar("toolchain", { length: 64 }).notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const reviewEvents = mysqlTable("review_events", {
  id: serial("id").primaryKey(),
  statementId: varchar("statement_id", { length: 64 }).notNull(),
  action: mysqlEnum("action", ["approved", "disputed", "draft", "ai_draft_created"])
    .notNull(),
  note: text("note").notNull(),
  actor: varchar("actor", { length: 128 }).default("Workshop reviewer").notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const aiDrafts = mysqlTable("ai_drafts", {
  id: serial("id").primaryKey(),
  statementId: varchar("statement_id", { length: 64 }).notNull(),
  proposedFormal: text("proposed_formal").notNull(),
  backTranslation: text("back_translation").notNull(),
  interpretationNotes: text("interpretation_notes").notNull(),
  status: mysqlEnum("status", ["pending", "accepted", "rejected"])
    .default("pending")
    .notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});
