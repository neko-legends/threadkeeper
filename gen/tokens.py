import sys
from .render import load_session, render_transcript, count_tokens
for p in sys.argv[1:]:
    t = render_transcript(load_session(p))
    print(p, len(t), *count_tokens(t))
