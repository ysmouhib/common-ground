import { drizzle } from "drizzle-orm/mysql2";
import { createPool } from "mysql2";
import { env } from "../lib/env";
import { log } from "../lib/logger";
import * as schema from "@db/schema";
import * as relations from "@db/relations";

const fullSchema = { ...schema, ...relations };

let instance: ReturnType<typeof drizzle<typeof fullSchema>>;

export function getDb() {
  if (!instance) {
    const pool = createPool({ uri: env.databaseUrl });
    // TIMESTAMP columns are sent and read as text in the session's time zone, and the
    // ORM reads that text as UTC. On a database server whose own zone is not UTC, every
    // stored time (review events, verification runs) came back shifted by the offset.
    // Pinning each session to UTC makes the text mean what the ORM assumes.
    pool.on("connection", (connection) => {
      connection.query("SET time_zone = '+00:00'", (error) => {
        if (error) log.warn("could not pin the database session to UTC; stored times may be shifted", { error: error.message });
      });
    });
    instance = drizzle(pool, {
      mode: "planetscale",
      schema: fullSchema,
    });
  }
  return instance;
}
