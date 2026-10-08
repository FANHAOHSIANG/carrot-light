#!/usr/bin/env bash
# SSH-only helper; C4 Custom Software requires the ELF file, not this script.
set -euo pipefail
export GIT_TERMINAL_PROMPT=0
if [ ! -f /AGNOS ]; then
  echo 'Carrot Light installer supports comma AGNOS devices only.'
  exit 1
fi
if [ -e /data/openpilot ] || [ -L /data/openpilot ]; then
  echo 'Existing /data/openpilot found. Use the device Software Uninstall flow first; nothing was removed.'
  exit 1
fi
INSTALL_STAGE=$(mktemp -d /data/carrot-light-install.XXXXXX)
trap 'rm -rf -- "$INSTALL_STAGE"' EXIT
# This branch contains the complete pinned official source plus ambientd.
git clone --depth 1 --branch carrot-wip --single-branch https://github.com/FANHAOHSIANG/carrot-light.git "$INSTALL_STAGE/openpilot"
test -f "$INSTALL_STAGE/openpilot/launch_openpilot.sh"
test -f "$INSTALL_STAGE/openpilot/openpilot/selfdrive/carrot/ambientd.py"
test -f "$INSTALL_STAGE/openpilot/carrot_light/UPSTREAM_COMMIT"
mv "$INSTALL_STAGE/openpilot" /data/openpilot
printf '#!/usr/bin/env bash\ncd /data/openpilot\nexec ./launch_openpilot.sh\n' > /data/continue.sh
chmod +x /data/continue.sh
sync
# No automatic reboot: the comma installer owns completion and reboot.
