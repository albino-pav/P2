#!/usr/bin/env bash

for llindar in $(LC_NUMERIC=C seq 2 0.05 3); do
	echo -ne "$llindar\t"
	scripts/run_vad.sh $llindar | grep TOTAL
done | sort -k2n -t:
