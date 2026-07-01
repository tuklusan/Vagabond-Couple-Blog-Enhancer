# TICKET-0103: Schema instrument uses method verb 'drove' instead of the Vehicle
Status: closed
Priority: critical
Type: bug
Created: 2026-07-01
Description: usa13v13 vs POSTED: schema instrument.name='drove' (the method verb) instead of the vehicle 'Shehzadi' (Toyota Tundra), which IS in the prose and even correct in the route box. schema_builder must build a Vehicle {name,manufacturer,model}; never the verb. Add vehicle extraction to context (regex/LLM: '<Name> (our ... Toyota Tundra)').
Steps to Reproduce: 
Notes: schema_builder._instrument builds a Vehicle from context['vehicle']; context_extractor.extract_vehicle mines 'Shehzadi (Toyota Tundra)' from prose. Never the method verb. Verified: instrument={name:Shehzadi,manufacturer:Toyota,model:Tundra}.
