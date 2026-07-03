# TICKET-0125: YouTube embed template shipped with baked-in Turkmenistan sample text instead of placeholders
Status: closed
Priority: Critical
Type: Bug
Created: 2026-07-03
Description: Config/workflow-docs/YOUTUBE-VIDEO-EMBED-FOR-BLOGGER.txt (a Required Project Document, in-repo) had its title attr and caption <p> filled with REAL sample content ('Morning departure from Khansar Family Yurt Camp near Aydarkul Lake...') instead of the [VIDEO TITLE]/[CAPTION TEXT] bracketed placeholders that assembler.py's reemit_youtube() looks for via .replace(). Since those literal tokens never appeared in the template, the .replace() calls were no-ops and EVERY post with a YouTube embed got the wrong, unrelated Turkmenistan/Uzbekistan yurt-camp title+caption baked into its own video embed -- only the video ID substitution worked (template also happened to ship a real ID that had its own literal .replace()). Discovered via arsenalna1 run: G2 Pass-1 correctly flagged the resulting embed as completely off-topic ('Khansar Family Yurt Camp' has nothing to do with a Kyiv metro station). USA-13 never surfaced this because that post had no YouTube embed. FIX: replaced template content with proper [VIDEO_ID]/[VIDEO TITLE]/[CAPTION TEXT] placeholder tokens; removed the now-dead legacy YJ354Qhiae0 literal-ID replace() in assembler.reemit_youtube(). Verify: re-run arsenalna1 and confirm the embed title/caption reflect the actual Arsenalna video.
Steps to Reproduce: 
Notes: Fixed and verified via arsenalna1 re-runs; deterministic test suites green.
