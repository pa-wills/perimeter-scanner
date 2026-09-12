#!/usr/bin/env bash
# recon-ng subdomain-enumeration workflow, run as a one-shot container task
# (ECS Fargate). Replaces the @reboot cron on the old EC2 worker.
#
# Environment (from the ECS task definition):
#   PSCAN_DOMAINS_TO_ENUMERATE   comma-separated list of domains
#   PSCAN_RECONNG_WORKSPACE      recon-ng workspace name
#   PSCAN_S3_BUCKET              bucket the results CSV is copied to
#
# Credits: https://safetag.org/activities/automated_recon and others (see git history).

set -euo pipefail

: "${PSCAN_DOMAINS_TO_ENUMERATE:?}" "${PSCAN_RECONNG_WORKSPACE:?}" "${PSCAN_S3_BUCKET:?}"

# $HOME/.recon-ng is a fresh, empty, writable tmpfs at container start (the task
# definition's root filesystem is read-only - ECS.5 - and recon-ng needs to write its
# keys/workspace DBs there). Re-seed it from the build-time copy (modules, marketplace
# registry, keys.db - see reconng/Dockerfile) before running anything, or every module
# load fails with "Invalid module name".
mkdir -p "$HOME/.recon-ng"
cp -a /opt/reconng-seed/. "$HOME/.recon-ng/"

WS="$PSCAN_RECONNG_WORKSPACE"
# split on comma; strip spaces/tabs only (NOT the newlines that separate the domains)
mapfile -t domains < <(tr ',' '\n' <<<"$PSCAN_DOMAINS_TO_ENUMERATE" | tr -d ' \t' | grep .)
[ "${#domains[@]}" -gt 0 ] || { echo "no domains in PSCAN_DOMAINS_TO_ENUMERATE" >&2; exit 1; }

recon() { recon-cli --no-version "$@"; }

# Fresh workspace
recon -C "workspaces remove $WS" || true
recon -C "workspaces create $WS"
recon -C "options set TIMEOUT 60"
sleep 5

# Seed the domains table
for d in "${domains[@]}"; do
  printf '%s\n\n' "$d" | recon -w "$WS" -C "db insert domains"
done
recon -w "$WS" -C "show domains"

# domains -> hosts (modules are baked into the image; see reconng/Dockerfile)
for mod in recon/domains-hosts/brute_hosts \
           recon/domains-hosts/hackertarget \
           recon/domains-hosts/certificate_transparency \
           recon/domains-hosts/bing_domain_web \
           recon/domains-hosts/google_site_web; do
  for d in "${domains[@]}"; do
    recon -w "$WS" -m "$mod" -c "options set SOURCE $d"
    recon -w "$WS" -m "$mod" -c "run"
    sleep 10
  done
done

# Forward-resolve every discovered host
recon -w "$WS" -m recon/hosts-hosts/resolve -c "run"

# Export to CSV
recon -w "$WS" -m reporting/csv -c "options set HEADERS True"
recon -w "$WS" -m reporting/csv -c "run"

csv="$HOME/.recon-ng/workspaces/$WS/results.csv"
aws s3 cp "$csv" "s3://$PSCAN_S3_BUCKET/"
rm -f "$csv"
