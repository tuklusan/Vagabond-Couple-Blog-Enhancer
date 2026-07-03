# TICKET-0119: Assembled HTML concatenated onto giant single lines
Status: closed
Priority: low
Type: improvement
Created: 2026-07-01
Description: Pre-fold->RAAG chunk is crammed onto one line (renders fine, hard to diff). Pretty-print the assembled HTML.
Steps to Reproduce: 
Notes: Fixed: assembler.reflow_blocks inserts newlines between DIRECTLY-ADJACENT block elements only (div/script/table/ol/h2/p/...), never inline tags (a/b/i/span), so the assembled source is readable/diffable while rendering identically. Wired into assemble() after normalize/strip. Verified: block boundaries separated, inline intact, G2 clean.
