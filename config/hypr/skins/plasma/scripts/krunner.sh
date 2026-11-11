#!/usr/bin/env bash
# BWM F12: native Plasma KRunner, unique D-Bus instance, no plasmashell dependency.
set -euo pipefail
exec krunner "$@"
