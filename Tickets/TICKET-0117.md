# TICKET-0117: Stray empty <p></p> after Route at a Glance
Status: closed
Priority: low
Type: bug
Created: 2026-07-01
Description: Assembler leaves an empty <p></p> after the RAAG <ol> (usa13v13 L156). Strip empty paragraphs in assembly.
Steps to Reproduce: 
Notes: assembler.strip_empty_paragraphs removes empty <p></p> (keeps <p><br/></p>). Applied in assemble().
