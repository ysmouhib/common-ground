# Golden corpus: the Swiss CO2 law votation of 13 June 2021 (vote 644)

The referendum on the revised CO2 law was rejected with 51.6 % No. The two camps
argued in the official voting booklet (swissvotes.ch, vote 644):

- **camp `yes`** — Bundesrat und Parlament (the Federal Council and Parliament),
  booklet p. 64–65 (DE), the "Ja" recommendation.
- **camp `no`** — the referendum committee (Wirtschaftskomitee «Nein zum
  CO2-Gesetz»), booklet p. 63 (DE), the "Nein" recommendation.

`statements.json` holds the first hand-worked statement list: 13 statements with
verbatim German text and their booklet page. Sources with URLs are in
`statements.json → vote.sources`. The French booklet (`brochure-fr.pdf`) covers
the same camps for the bilingual annotation (Phase 7, CG7-2).

`golden.json` (added by CG7-2) will hold the hand-worked target output: FOL
formalizations of the statements, candidate axioms per camp, and the expected
load ranking, which the pipeline must then reproduce (CG7-3).

This is seed data under `examples/` per the build brief §6: the pipeline runs on
it headless, and Phase 8's holdout test withholds statements of a camp and
checks that the extracted axiom system still derives them.
