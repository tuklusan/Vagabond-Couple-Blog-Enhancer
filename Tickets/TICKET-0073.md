# TICKET-0073: [schema_builder.py] XSS vulnerability via unescaped JSON in script tag
Status: closed
Priority: High
Type: Bug
Created: 2026-07-01
Description: The build_schema_script function directly inserts JSON into a <script> tag without escaping '</script>' sequences. If any schema value (e.g., description, name, origin) contains '</script>', it breaks the script tag and enables script injection. This is a classic XSS vector when embedding JSON in HTML. | Suggestion: After serializing the JSON, replace '</' with '<\/' to prevent early closing of the script tag. For example: body = json.dumps(schema, ensure_ascii=False, indent=indent).replace('</', '<\/') | File: orchestrator/schema_builder.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed: build_schema_script escapes '</' -> '<\/' so a schema value containing </script> cannot close the tag early; JSON still parses (verified with a </script>-laden value). Defense-in-depth XSS fix.
