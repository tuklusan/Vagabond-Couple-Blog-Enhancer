# TICKET-0090: [assembler.py] Incorrect placement of pre-fold content when <!--more--> is missi
Status: closed
Priority: High
Type: Bug
Created: 2026-07-01
Description: In apply_prefold(), if _find_more_comment() returns None, a new <!--more--> comment is appended to the end of the document (soup.append(more)). Subsequent insert_before() calls place the summary block and schema just before this end-of-document marker, effectively putting them at the very bottom of the post body instead of after introductory paragraphs. This violates the intended pre-fold layout and breaks the post structure. | Suggestion: Insert the new <!--more--> after the introductory paragraphs (e.g., after the first few <p> elements or after the first heading) instead of appending to the entire document. A simple heuristic: find the first <h2> and insert before it, or if none, after the first few <p> tags. | File: orchestrator/assembler.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed: apply_prefold now places a missing <!--more--> at the END OF THE PRE-FOLD ZONE (before the first section <h2>, else after the intro paragraphs, else append) instead of appending to the whole document -- so summary block + schema land in the pre-fold zone, not at the post bottom. Regression test added; schema_ok/summary_present/more_canonical verified.
