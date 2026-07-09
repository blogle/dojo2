# Assets and Liabilities Domain Notes

dojo keeps all financial entities under one account identity, but different account classes have different rules.

Budget accounts are inside the budget. They appear in the normal transaction ledger, affect categories, and contribute to net worth from ledger-derived balances. Credit cards are budget accounts with special linked payment-category behavior.

Tracking accounts are simple snapshot accounts outside the budget. Aspire net-worth categories import as tracking accounts unless they duplicate a budget account. Tracking accounts use their latest snapshot value and have an explicit asset or liability polarity.

Investment accounts are richer non-budget assets. Their value comes from holdings plus cash. Holdings store ticker, quantity, and average basis. Prices are stored separately so brokerage statement prices can prove reconciled values and future market prices can support current estimates. Investment accounts carry self-managed flag and tax treatment metadata for portfolio and withdrawal planning.

Loans are richer liabilities. A loan has details such as original amount and rate when known, plus principal-balance snapshots. Mortgage or loan budget categories plan cash obligations, but ordinary category transactions do not change loan balances by themselves.

Tangible assets are non-budget assets such as homes or vehicles. They use valuation snapshots and do not create budget activity when their value changes.

Account-budget links explain how an account relates to a budget category. Credit-card links and investment contribution links can create derived budget activity from ledger rows. Loan links are planning context for now; loan balances change through balance snapshots and reconciliation, not from ordinary category spend.

Derived budget activity is computed from existing ledger rows and links. dojo does not create hidden transaction rows for derived activity.

Reconciliation records that an account or entity was checked against a source of truth as of a date. Reconciliation does not own the account data. It stores lightweight evidence pointing at the versioned records that were verified.

When importing Aspire data, dojo preserves history instead of guessing richer behavior. Aspire budget accounts become budget accounts. Aspire net-worth categories become tracking accounts. Users can later create investment accounts, loans, or tangible assets and cut over from old tracking accounts when they are ready.
