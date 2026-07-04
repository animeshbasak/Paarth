# income:mvp-scope

> [income] Cuts a product or client build to the smallest slice that earns money or proof — walking skeleton, fake-it list, first-dollar path. Triggers on "mvp", "smallest version", "scope cut", "descope", "what can I ship in two weeks", "lean build".

# income:mvp-scope

Origin: first-party PAARTH skill (not vendored). The counterweight to feature
creep: define the smallest build that produces revenue or a validated learning.

## Procedure

1. **State the first dollar.** One sentence: who pays (or commits), for what,
   through which mechanism (Stripe link, invoice, LOI, waitlist deposit). If the
   answer is "nobody yet", route to income:validate-idea first — an MVP without a
   payer definition is a prototype, not a product.
2. **Walking skeleton.** List the end-to-end happy path as user-visible steps
   (max 7). The MVP is exactly these steps working once, for one user segment, on
   one platform. Everything else is a later milestone.
3. **Fake-it list.** For each step, ask: can this be manual, hardcoded, or a
   third-party tool for the first 10 customers? Auth → magic link only. Admin →
   a spreadsheet. Billing → payment link. Notifications → you, manually. Write
   the fake next to each step; automating a fake before 10 customers is scope creep.
4. **Cut list with re-entry criteria.** Every cut feature gets one line: what was
   cut + the observable trigger that re-adds it ("add team accounts when 3 paying
   users ask"). This makes cuts feel reversible, which is what makes them stick.
5. **Two-week test.** If the skeleton + fakes still exceed ~2 weeks of the user's
   real available hours, cut the segment (narrower who) before cutting steps.
   When the user has a stack preference on file, estimate against that stack.
6. **Definition of shipped.** The MVP is done when one real outside person
   completes the happy path and the first-dollar mechanism has been exercised at
   least once (even at $1). Demo-to-friends does not count.

## Verification

The scope passes when: the happy path is ≤7 steps; every step has either real
code or a named fake; the cut list is longer than the build list; first-dollar
mechanism is concrete (a URL or an invoice template, not "we'll charge later").
