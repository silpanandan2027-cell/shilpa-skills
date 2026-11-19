"""Starts Clips Kitty's MCP server without installing its engine's packages.

Clips Kitty's own `python main.py mcp` imports the whole pipeline first
(numpy, OpenCV, PyTorch...), but the MCP server itself (server/mcp.py) uses
only the standard library: it just talks to the running app on 127.0.0.1:8765.
So this loads that one module from a source checkout and serves it. It works
with any copy of the app (Microsoft Store, winget, installer or source).

Checkout location: CLIPS_KITTY_SRC, else ~/.shilpa-clippers/clips-studio
(the installers put it there).
"""

import os
import sys
from pathlib import Path

src = Path(os.environ.get("CLIPS_KITTY_SRC") or Path.home() / ".shilpa-clippers" / "clips-studio")
if not (src / "server" / "mcp.py").is_file():
    sys.stderr.write(f"Clips Kitty source not found at {src}. Run the shilpa-skills installer again.\n")
    sys.exit(1)
sys.path.insert(0, str(src))
from server.mcp import serve  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.exit(serve())
