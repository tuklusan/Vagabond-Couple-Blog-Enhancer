# TICKET-0181: [test_sequencer.py] test_g4_step_entry_gate expects halt at wrong node
Status: Closed
Priority: High
Type: Task
Created: 2026-07-04
Description: The test asserts that the sequencer halts at nodeB ('g4_blocks_nodeB'), but nodeA is intentionally incomplete. If the gate logic halts when a node returns incomplete, the halt should occur at nodeA. This assertion likely fails or validates incorrect behavior. | Suggestion: Verify the intended behavior of run_sequence: if it sets 'at' to the current node that caused the halt, change the expected node to 'nodeA'. If the logic intentionally advances the index, document it and adjust the test name accordingly. | File: tests/test_sequencer.py | Severity: critical
Steps to Reproduce: 
Notes: FALSE POSITIVE, NO ACTION. The reviewer misread the G4 semantics: rule G4 is a step-ENTRY gate -- 'no node may BEGIN until the prior node is confirmed complete'. A node returning complete=False does not halt at itself (it may legitimately be awaiting an operator, a retry, etc.); the halt fires when the NEXT node attempts to enter, and the halt record correctly reports at=nodeB with item=nodeA ('complete nodeA before nodeB'). The test asserts exactly this designed, long-standing behavior (unchanged since the Phase-D sequencer work) and passes deterministically -- the reviewer's 'likely fails' speculation is refuted by the green suite. No change made.
