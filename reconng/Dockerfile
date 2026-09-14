# recon-ng subdomain-enumeration worker - a one-shot ECS Fargate task image.
# Replaces the EC2 WorkerInstance that used to run enumerateSubdomains.bash
# from a @reboot cron.
#
# Inspector (ECR image scanning) reports ~21 findings (7 HIGH) as of 2026-09-12, all
# in this base image's own bundled OS libraries (libxml2, pcre2, sqlite3, gzip, zlib,
# nghttp2) - none in recon-ng's own REQUIREMENTS or awscli. (pip itself had 6 more,
# fixed below by upgrading it.) Accepted risk: nothing here installs or controls those
# packages directly, and several have no upstream fix published yet at all. `--pull`
# in buildspec.yaml ensures the next build picks up whatever Debian has patched by
# then automatically. See #52.
FROM public.ecr.aws/docker/library/python:3.12-slim

ENV HOME=/opt/reconng \
    PATH=/opt/recon-ng:$PATH \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# recon-ng ref to build from. The project tags releases rarely; pin this to a
# commit SHA once a build is validated for full reproducibility.
ARG RECONNG_REF=master

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      git ca-certificates build-essential libxml2-dev libxslt1-dev \
 && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch "${RECONNG_REF}" \
      https://github.com/lanmaster53/recon-ng.git /opt/recon-ng \
 && pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /opt/recon-ng/REQUIREMENTS awscli

# Run as non-root; recon-ng writes its db / workspaces / modules under $HOME/.recon-ng.
RUN useradd --system --home-dir /opt/reconng --create-home reconng \
 && chown -R reconng:reconng /opt/reconng /opt/recon-ng
USER reconng

# Bake in the marketplace modules the workflow uses, so runtime is deterministic
# and does not depend on the marketplace being reachable.
RUN recon-cli --no-version -C "marketplace refresh" \
 && for m in recon/domains-hosts/brute_hosts \
             recon/domains-hosts/hackertarget \
             recon/domains-hosts/certificate_transparency \
             recon/domains-hosts/bing_domain_web \
             recon/domains-hosts/google_site_web \
             recon/hosts-hosts/resolve \
             reporting/csv ; do \
      recon-cli --no-version -C "marketplace install $m" ; \
    done

# Preserve the build-time-populated $HOME/.recon-ng (modules, marketplace registry,
# keys.db) at a separate path. The runtime task definition mounts a fresh, empty,
# writable tmpfs at $HOME/.recon-ng (needed for ECS.5 - read-only root filesystem -
# since recon-ng writes its keys/workspace DBs there); that mount would otherwise
# shadow everything baked in above. enumerateSubdomains.bash re-seeds the tmpfs from
# this copy on every container start, before running anything.
USER root
RUN cp -a /opt/reconng/.recon-ng /opt/reconng-seed \
 && chown -R reconng:reconng /opt/reconng-seed
USER reconng

COPY --chown=reconng:reconng enumerateSubdomains.bash /opt/reconng/enumerateSubdomains.bash
ENTRYPOINT ["bash", "/opt/reconng/enumerateSubdomains.bash"]
