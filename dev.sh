#!/bin/bash
# Forward all arguments directly to development.sh
exec "$(dirname "$0")/development.sh" "$@"
