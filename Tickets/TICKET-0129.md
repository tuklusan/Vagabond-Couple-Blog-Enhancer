# TICKET-0129: step7 route summary box hardcoded 'Vehicle:' field, looped/halted when no vehicle exists
Status: closed
Priority: High
Type: Bug
Created: 2026-07-03
Description: step7_route_summary_box's deterministic check hard-required a literal 'Vehicle:' field in the route summary box, even for posts with no personal vehicle (context['vehicle'] empty -- a metro/transit/on-foot post). On the arsenalna1 run the writer correctly tried to describe transit instead of a nonexistent vehicle, but the deterministic check kept failing it for missing 'Vehicle:', looping through MAX_NODE_ROUNDS and ESCALATING to an operator abort. FIX: added _last_label(context) -- 'Vehicle:' only when context['vehicle'] is truthy, else the neutral 'Transit:' (matching how the human POSTED workflow labels a non-road-trip post), and threaded it through the writer prompt/user-context and the deterministic field check. Verify: re-run arsenalna1, confirm step7 certifies without looping and uses 'Transit:' not a fabricated vehicle.
Steps to Reproduce: 
Notes: Fixed and verified via arsenalna1 re-runs; deterministic test suites green.
