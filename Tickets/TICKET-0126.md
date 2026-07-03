# TICKET-0126: reemit_youtube caption extraction misses legacy plain-text-after-<br/> captions
Status: Open
Priority: Medium
Type: Improvement
Created: 2026-07-03
Description: assembler.reemit_youtube() only looks for a <p class='tr-caption'> inside the embed wrapper to source the video title/caption. Legacy Blogger video embeds (e.g. arsenalna-metro-kyiv-original) instead put the caption as plain text directly after a <br/> inside the .separator div: '<iframe ...></iframe><br />Watch:&nbsp;Exploring WORLD'S DEEPEST METRO STATION:...'. No <p class=tr-caption> exists, so caption stays empty and the embed falls back to the generic title='Video'/empty caption in the output, instead of a real descriptive title. Observed on arsenalna1 run (TICKET-0125 verification). Fix: when no tr-caption <p> is found, fall back to any non-empty trailing text content of the wrapper/iframe's parent (the text after the iframe tag) as the caption source.
Steps to Reproduce: 
Notes: 
