# TICKET-0109: Schema from/toLocation under-specified (no full names / containedInPlace)
Status: closed
Priority: high
Type: improvement
Created: 2026-07-01
Description: from='Oakhurst, CA' to='Grand Canyon, AZ'; POSTED='Oakhurst, California, USA' / 'Grand Canyon Village, Arizona, USA' with containedInPlace Coconino County. Normalize to full place names (expand state abbrev, add USA) and add containedInPlace where known.
Steps to Reproduce: 
Notes: schema_builder._full_place_name expands trailing state abbrev (CA->California) and appends USA. Verified 'Oakhurst, California, USA' / 'Grand Canyon, Arizona, USA'. (containedInPlace county deferred -- needs a lookup table.)
