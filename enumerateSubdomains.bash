#! /usr/bin/bash

# Surveillance script. Presumes recon-ng is installed (which it ought to be)

# Credits:
# https://safetag.org/activities/automated_recon
# https://medium.com/hacker-toolbelt/recon-ng-how-to-iii-bf42b6fbc82b
# https://warroom.rsmus.com/footprinting-the-target-with-recon-ng/




cd /home/ec2-user/recon-ng/
/home/ec2-user/recon-ng/recon-cli -C "workspaces remove nbnco" --no-version
/home/ec2-user/recon-ng/recon-cli -C "workspaces create nbnco" --no-version
/home/ec2-user/recon-ng/recon-cli -C "workspaces list" --no-version
/home/ec2-user/recon-ng/recon-cli -C "options set TIMEOUT 60" --no-version
sleep 10

/home/ec2-user/recon-ng/recon-cli -C "marketplace install brute_hosts" --no-version
/home/ec2-user/recon-ng/recon-cli -C "modules load brute_hosts" --no-version
/home/ec2-user/recon-ng/recon-cli -w nbnco -m recon/domains-hosts/brute_hosts -c "options set SOURCE nbnco.com.au" --no-version
/home/ec2-user/recon-ng/recon-cli -w nbnco -m recon/domains-hosts/brute_hosts -c "run" --no-version
sleep 10
/home/ec2-user/recon-ng/recon-cli -w nbnco -m recon/domains-hosts/brute_hosts -c "options set SOURCE nbnco.net.au" --no-version
/home/ec2-user/recon-ng/recon-cli -w nbnco -m recon/domains-hosts/brute_hosts -c "run" --no-version
sleep 10

/home/ec2-user/recon-ng/recon-cli -C "marketplace install hackertarget" --no-version
/home/ec2-user/recon-ng/recon-cli -C "modules load hackertarget" --no-version
/home/ec2-user/recon-ng/recon-cli -w nbnco -m recon/domains-hosts/hackertarget -c "options set SOURCE nbnco.com.au" --no-version
/home/ec2-user/recon-ng/recon-cli -w nbnco -m recon/domains-hosts/hackertarget -c "run" --no-version
sleep 10
/home/ec2-user/recon-ng/recon-cli -w nbnco -m recon/domains-hosts/hackertarget -c "options set SOURCE nbnco.net.au" --no-version
/home/ec2-user/recon-ng/recon-cli -w nbnco -m recon/domains-hosts/hackertarget -c "run" --no-version
sleep 10

/home/ec2-user/recon-ng/recon-cli -C "marketplace install certificate_transparency" --no-version
/home/ec2-user/recon-ng/recon-cli -C "modules load certificate_transparency" --no-version
/home/ec2-user/recon-ng/recon-cli -w nbnco -m recon/domains-hosts/certificate_transparency -c "options set SOURCE nbnco.com.au" --no-version
/home/ec2-user/recon-ng/recon-cli -w nbnco -m recon/domains-hosts/certificate_transparency -c "run" --no-version
sleep 10

# TODO: This is _not_ working. Why?
/home/ec2-user/recon-ng/recon-cli -m recon/domains-hosts/certificate_transparency -c "options set SOURCE nbnco.net.au" --no-version
/home/ec2-user/recon-ng/recon-cli -m recon/domains-hosts/certificate_transparency -c "run" --no-version
sleep 10

/home/ec2-user/recon-ng/recon-cli -C "marketplace install bing_domain_web" --no-version
/home/ec2-user/recon-ng/recon-cli -C "modules load bing_domain_web" --no-version
/home/ec2-user/recon-ng/recon-cli -w nbnco -m recon/domains-hosts/bing_domain_web -c "options set SOURCE nbnco.com.au" --no-version
/home/ec2-user/recon-ng/recon-cli -w nbnco -m recon/domains-hosts/bing_domain_web -c "run" --no-version
/home/ec2-user/recon-ng/recon-cli -w nbnco -m recon/domains-hosts/bing_domain_web -c "options set SOURCE nbnco.net.au" --no-version
/home/ec2-user/recon-ng/recon-cli -w nbnco -m recon/domains-hosts/bing_domain_web -c "run" --no-version

/home/ec2-user/recon-ng/recon-cli -C "marketplace install google_site_web" --no-version
/home/ec2-user/recon-ng/recon-cli -C "modules load google_site_web" --no-version
/home/ec2-user/recon-ng/recon-cli -w nbnco -m recon/domains-hosts/google_site_web -c "options set SOURCE nbnco.com.au" --no-version
/home/ec2-user/recon-ng/recon-cli -w nbnco -m recon/domains-hosts/google_site_web -c "run" --no-version
/home/ec2-user/recon-ng/recon-cli -w nbnco -m recon/domains-hosts/google_site_web -c "options set SOURCE nbnco.net.au" --no-version
/home/ec2-user/recon-ng/recon-cli -w nbnco -m recon/domains-hosts/google_site_web -c "run" --no-version

/home/ec2-user/recon-ng/recon-cli -C "marketplace install csv" --no-version
/home/ec2-user/recon-ng/recon-cli -C "modules load reporting/csv" --no-version
/home/ec2-user/recon-ng/recon-cli -w nbnco -m reporting/csv -c "options set HEADERS True" --no-version
/home/ec2-user/recon-ng/recon-cli -w nbnco -m reporting/csv -c "run" --no-version
aws s3 cp /home/ec2-user/.recon-ng/workspaces/nbnco/results.csv s3://test-scanner-resultsbucket-5ev654hjwnmb
rm /home/ec2-user/.recon-ng/workspaces/nbnco/results.csv

# TODO: take the name of the s3 bucket from aws itself, not set it statically. This is a crude hack.





