# Example ClickUp task: Search must preserve filters

Use only after introducing a controlled regression on a dedicated demo branch.

## Reproduction

1. Open the demo support inbox.
2. Set status to Open and priority to High.
3. Search for report.
4. Clear the search text.

## Expected

Status remains Open, priority remains High, and only ticket #1042 is shown. Changing the search must not change either filter.

## Evidence required

Failing reproduction on the affected commit; passing independent browser acceptance check after the fix; full verification output; PR linked to this task; before/after trace or screenshots. If no regression can be reproduced, report that outcome instead of making an unrelated change.
