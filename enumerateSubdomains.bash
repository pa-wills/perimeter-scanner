#! /usr/bin/bash

# Surveillance script. Presumes recon-ng is installed (which it ought to be)

cd /home/ec2-user/recon-ng/
/home/ec2-user/recon-ng/recon-cli -C "workspaces remove nbnco" --no-version
/home/ec2-user/recon-ng/recon-cli -C "workspaces create nbnco" --no-version
/home/ec2-user/recon-ng/recon-cli -C "workspaces list" --no-version

/home/ec2-user/recon-ng/recon-cli -C "marketplace install hackertarget" --no-version
/home/ec2-user/recon-ng/recon-cli -C "modules load hackertarget" --no-version
/home/ec2-user/recon-ng/recon-cli -m recon/domains-hosts/hackertarget -c "options set SOURCE nbnco.com.au" --no-version
/home/ec2-user/recon-ng/recon-cli -m recon/domains-hosts/hackertarget -c "run" --no-version
/home/ec2-user/recon-ng/recon-cli -m recon/domains-hosts/hackertarget -c "options set SOURCE nbnco.net.au" --no-version
/home/ec2-user/recon-ng/recon-cli -m recon/domains-hosts/hackertarget -c "run" --no-version

/home/ec2-user/recon-ng/recon-cli -C "marketplace install certificate_transparency" --no-version
/home/ec2-user/recon-ng/recon-cli -C "modules load certificate_transparency" --no-version
/home/ec2-user/recon-ng/recon-cli -m recon/domains-hosts/certificate_transparency -c "options set SOURCE nbnco.com.au" --no-version
/home/ec2-user/recon-ng/recon-cli -m recon/domains-hosts/certificate_transparency -c "run" --no-version