# Personal Operations — Deadline & Compliance Tracker
> Auto-checked daily at 9 AM ET by deadline monitor job.
> Update when new deadlines are discovered. NEVER delete resolved items — mark as DONE.

## Active Deadlines

### Immigration / Legal
- **Green Card**: USCIS# 220-415-756, Category E37, exp ~06/07/2032
  - Status: ACTIVE
  - Next action: None until renewal window (~2031)

### Insurance
- **Health**: Anthem Blue Cross PPO, Member ID JPU099M91022, Group L03869M007
  - Status: VERIFY — likely COBRA post-Roblox. Anthem sent secure portal message Mar 17. EOBs still generating (Mar 5, Feb 10) = coverage active.
  - Action needed: Log into anthem.com/ca to read Mar 17 secure message (may be COBRA expiration notice). Check coverage end date.
- **Renters**: Lemonade LP7985579E4
  - Status: CANCELLED — Idam confirmed cancelled March 31, 2026.
  - Note: Playwright verification on Apr 3 showed policies as active (lazy-load UI), but Idam explicitly stated cancellation. Nechev's Apr 4 response references insurance cancellation.
  - Action needed: None (cancelled by design on move-out).

### Medi-Cal (confirmed 2026-04-21)
- BIC: 97918535H16086 (in MEMORY-PRIVATE.md)
- Issued: 03/27/2026 (recent — may be initial enrollment)
- Status: ACTIVE. Beneficiary portal login confirmed 2026-04-21 (creds in MEMORY-PRIVATE.md).
- Apr 16 Medi-Cal Rx welcome email was legitimate, not misrouted.
- Implication: Schedule II stimulant Rx likely needs Medi-Cal Rx prior authorization. Multiple pharmacy rejections through Apr may stem from PA never being submitted by prescriber (Mutiat Olawunmi @ MEDvidi).

### MEDvidi Rx failure-mode taxonomy (learned 2026-04-21)
When an Rx is "stuck," diagnose WHICH of these 3 failures — they require different fixes. Do NOT conflate them.
1. **Compliance-docs block** (ticket 55196, Apr 9): pharmacy asks how provider is monitoring a Schedule II patient (BP/HR/weight). Fix: provider attaches monitoring-plan notation. Failure mode if ignored: pharmacy sits on Rx indefinitely, doesn't return it.
2. **Formulary refusal** (ticket 56379, Apr 16): pharmacy categorically doesn't dispense the drug class ("we don't dispense lisdexamfetamine"). Fix: retarget to a different pharmacy entirely. Not fixable by more paperwork.
3. **Verification-hold timeout** (inferred Apr 17-20): pharmacy's corresponding-responsibility call goes unanswered within 3-5 business days (21 CFR 1306.04) → Rx auto-returned/cancelled. Fix: pre-attach ICD-10 + monitoring plan + callback line in Rx notes so no call is needed; AND provider is reachable if one fires.
4. **Insurance-issue / coverage-hold** (Apr 22 Walgreens email): pharmacy can't adjudicate the claim. Fix: call pharmacy, provide current insurance details (Medi-Cal BIC 97918535H16086 issued 03/27/2026). IMPORTANT: distinguish "missing insurance on file" (pharmacy fix, give BIC) from "prior authorization required" (prescriber fix — MEDvidi 504-414-5095). Always ask the pharmacy which on the call — they are different downstream paths.
- **Plan B pharmacies pre-vetted**: Costco #144 (450 10th St SF, 415-437-2620) + Safeway #2606 (298 King St SF, 415-633-1020) — use if Walgreens #01297 hits another block.
- **MEDvidi supervisor line**: (504) 414-5095. Main (415) 966-0848 only routes to portal form, not a human.


### Pet Care
- **Gali rabies vaccine**: Next booster ~03/2027
  - Status: DONE — Completed Mar 19, 2026
  - Vet: SoMa Animal Hospital, 1110 4th St, SF — (415) 727-9116
  - Cancellation policy: 24hrs notice or $95 fee

### Utilities
- **Eversource electric**: Account 74019022172, confirmation 2026-0672158
  - Status: CANCELLED — Idam not pursuing (Mar 16, 2026)

### Financial
- **Chase Chargeback**: $500 + $1,545 Colombia trek charges (TourHero Inc)
  - Status: CANCELLED — Idam decided not to pursue (Mar 16, 2026)

### Tax (Federal)
- **2025 Federal Income Tax (1040)**: Due April 15, 2026
  - Status: FILED — Return signed 2026-03-23. $91,647 owed ($88K federal + $3.5K CA).
  - Installment plan needed (can't pay lump sum). Schedule C still pending.
  - Action needed: Set up IRS installment agreement before April 15. Timeline through Oct 2026.
- **2026 Q1 Estimated Tax (1040-ES)**: Due April 15, 2026
  - Status: PENDING — only if self-employment income in Q1 (Kyma has no revenue yet, likely $0)

### Incorporation — KYMA COMPUTER, INC. (renamed from KYMASTREAM on 2026-03-18)
- **Delaware Filing**: Harvard Business Services, Green + same-day ($379)
  - Status: DONE — Filed Mar 26, 2026. KYMA COMPUTER, INC. incorporated in Delaware. File #10556683.
  - Contact: Kathleen at kathleen@delawareinc.com, HBS: (800) 345-2677
  - Structure: 10M common + 10M preferred, $0.00001 par
  - Action needed: None — filing complete
- **Clerky Setup**: VC Post-Incorporation (Standard with Stock Plan)
  - Status: DONE — $819 paid Apr 8 (net $719 after $100 VC discount refund). 18 documents finalized.
  - Stock plan adopted. Equity compensation products unlocked. SAFEs/convertible notes available.
  - Domestic partner: Michael Young recommends listing Apolline — DECISION PENDING from Idam.
- **83(b) Elections**: FILED via Clerky managed add-on
  - Status: DONE — Both founders filed Apr 9, 2026. $149 each ($298 total).
  - Clerky handles: Priority Mail + Certified Mail to IRS Ogden UT, physical postmark, return receipt, scan + upload.
  - IRS filing deadline: ~May 8, 2026 (30 days from Apr 8 stock issuance). Filed well within window.
  - Share payment: Both founders owe $45.00 each (4.5M × $0.00001) via ACH/check to Mercury account. IN PROGRESS.
- **EIN Application**: DONE (2026-03-30). EIN 41-5195123, CP-575 downloaded.
- **Mercury Bank Account**: DONE (2026-03-30). Account opened, 2FA saved.
- **Venturous Counsel**: SIGNED (2026-04-02). Corporate records uploaded to Dropbox extranet. Awaiting audit + kick-off call.
- **Equity Split**: 50/50 with Apolline, 4yr vesting, 1yr cliff, double trigger acceleration
  - Status: NEEDS CONFIRMATION with Apolline

### Housing
- **Quincy SF**: 555 Bryant St, Unit 0918, San Francisco, CA 94107
  - Status: New address
  - Rent due: April 1, $4,101.68 total (via Conservice)
- **Verra Allston**: 50 Western Ave, Unit 1132H — demand letter situation
  - Status: MONITOR

## Completed / Resolved
<!-- Move resolved items here with date or delete if not needed to remember long term -->
