# TICKET-0104: Schema hasPart contains garbage 'CA'/'AZ' entities + duplicates
Status: closed
Priority: critical
Type: bug
Created: 2026-07-01
Description: build_haspart split 'Fresno, CA' into Places 'Fresno' and 'CA' (also 'AZ'); plus duplicate 'Fresno'/'Fresno, CA'. Never split 'City, ST'; drop 2-letter state fragments; dedupe by normalized name.
Steps to Reproduce: 
Notes: build_haspart: skip 2-letter state fragments, dedupe by leading place token, re-pair 'City, ST' in the landmarks string. Verified: no CA/AZ garbage; 18->11 entities.
