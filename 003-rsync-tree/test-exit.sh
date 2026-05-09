#!/bin/bash
set -x

echo "start"
( echo "subshell start"; exit 1; echo "subshell end" )
echo "after subshell, \$?=$?"
exit 1
