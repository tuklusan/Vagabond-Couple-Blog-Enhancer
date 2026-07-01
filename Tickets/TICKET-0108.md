# TICKET-0108: Schema hasPart legs lack descriptions; missing Road/Attraction entities
Status: closed
Priority: high
Type: improvement
Created: 2026-07-01
Description: hasPart legs are bare section titles (no description); POSTED legs carry fact-filled descriptions, plus Road entities (Route 66, I-40, AZ-64, CA-99) and TouristAttractions (Squire Resort, Kelso Dunes) mined from prose. Generate/carry leg descriptions and mine roads/attractions.
Steps to Reproduce: 
Notes: schema_builder now (a) gives each section-leg a fact-list description from its bolded/link proper nouns; (b) mines Road entities (Route 66, I-40, CA-99, AZ-64, US-89) and TouristAttractions (Squire Resort, Kelso/Mojave Preserve, Kaibab Forest, Yosemite/Grand Canyon Railway, Ludlow Cafe) from prose. Verified on v13 HTML: 6 legs+descriptions, 7 roads, 6 attractions (matches/exceeds POSTED).
