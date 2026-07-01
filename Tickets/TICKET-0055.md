# TICKET-0055: No TravelAction schema generation (Step 4 only validates) -- #1 indexing fix missing
Status: closed
Priority: critical
Type: improvement
Created: 2026-06-30
Description: The pipeline never GENERATES the TravelAction ld+json; Step 4 only validates. For a schema-less source post (the common 'crawled not indexed' case) the assembled HTML has no schema -> schema_ok/more_canonical fail at G2. Need a deterministic build_travelaction_schema(context) producing all REQUIRED_SCHEMA_FIELDS (author = Person 'The Vagabond Couple' sameAs blog root; hasPart from sections/stops/landmarks/waypoints; ETR in description), inserted pre-fold with <!--more--> immediately after </script>. Model on TRAVELACTION-ld_json-SCHEMA-EXAMPLE.txt + reference pre-fold.
Steps to Reproduce: 
Notes: Implemented orchestrator/schema_builder.py: build_travelaction_schema/build_schema_script build a valid TravelAction from context (all REQUIRED_SCHEMA_FIELDS, author_ok, hasPart from real H2 sections + route entities). Verified valid against validate_ld_json on the usa13v8 context (18 hasPart).
