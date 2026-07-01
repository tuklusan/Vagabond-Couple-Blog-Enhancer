# TICKET-0115: Non-breaking hyphens (U+2011) in generated text
Status: closed
Priority: medium
Type: bug
Created: 2026-07-01
Description: Generated fragments contain U+2011 non-breaking hyphens (sun-scorched, I-40, oil-rich). Normalize to plain '-' in generated content.
Steps to Reproduce: 
Notes: assembler.normalize_characters replaces U+2011/U+2010/hyphen-bullet with '-' and nbsp with space (en/em dashes kept). Applied in assemble(). Verified.
