# TICKET-0122: Summary block: truncated row + literal [POST TITLE] placeholder pass deterministic check
Status: closed
Priority: high
Type: bug
Created: 2026-07-02
Description: usa13v14 (auto instruct model): step3 output was truncated mid-row ('? | A Luxurious' -- 6th row cut off by the writer) AND echoed the literal '[POST TITLE]' placeholder. The deterministic check counted 6 rows (passed) and the reviewer certified; only Pass-1 caught the broken markup. Fix: step3 deterministic check now rejects rows lacking a ' - ' descriptor (truncation) and rejects a literal '[POST TITLE]'/'POST TITLE]'; prompt hardened to use the ACTUAL title and never cut a row. Verified against the v14 output.
Steps to Reproduce: 
Notes: Fixed + pushed: step3 deterministic check rejects truncated rows (no ' - ' descriptor) and literal [POST TITLE]; prompt hardened. Verified the v14 defective output is now caught at the gate.
