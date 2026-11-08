import { ensureSeeded } from "./seed-logic";

async function seed() {
  console.log("Seeding the sourced plastic-policy debate...");
  await ensureSeeded();
  console.log("Done. Existing review decisions were left unchanged.");
  process.exit(0);
}

seed().catch((error) => {
  console.error(error);
  process.exit(1);
});
