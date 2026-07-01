# TICKET-0056: Assembler drops summary block when source has none (no pre-fold insertion)
Status: closed
Priority: critical
Type: improvement
Created: 2026-06-30
Description: splice_fragments only REPLACES an existing summary block; for a summary-less post the step3 fragment is dropped and never rendered. Also step3 output is raw LABEL/NARRATIVE/ROWS text, not canonical HTML. Need: parse the fragment into (label, narrative, rows), render via canonical_summary_block, and INSERT it in the pre-fold zone (after intro paragraphs, before the schema). Then summary_present passes.
Steps to Reproduce: 
Notes: Implemented assembler.apply_prefold + parse_summary_fragment: parses the Step-3 fragment into the canonical summary block and inserts it (when the source lacks one) together with the generated schema, with <!--more--> immediately after </script>. Fixed loose <!--more--> detection (_find_more_comment matches content=='more', not any comment mentioning 'more'). Verified on usa13v8: schema_ok/summary_present(6 rows)/more_canonical all pass; only content checks (0054) remain. Tests green.
