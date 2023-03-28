#! /usr/bin/bash

# Surveillance script. Presumes recon-ng is installed (which it ought to be)

# Credits:
# https://safetag.org/activities/automated_recon
# https://medium.com/hacker-toolbelt/recon-ng-how-to-iii-bf42b6fbc82b
# https://warroom.rsmus.com/footprinting-the-target-with-recon-ng/
# https://tremblinguterus.blogspot.com/2019/11/advanced-reconnaissance-with-recon-ng.html


# Note relies on ENV VARs set by EC2 at launchtime. Specifically: PSCAN_RECONNG_WORKSPACE, PSCAN_S3_BUCKET, etc.
. ~/.bash_profile
domains=$(echo $PSCAN_DOMAINS_TO_ENUMERATE | tr "," "\n")


# Start with a fresh workspace
cd /home/ec2-user/recon-ng/
/home/ec2-user/recon-ng/recon-cli -C "workspaces remove $PSCAN_RECONNG_WORKSPACE" --no-version
/home/ec2-user/recon-ng/recon-cli -C "workspaces create $PSCAN_RECONNG_WORKSPACE" --no-version
/home/ec2-user/recon-ng/recon-cli -C "workspaces list" --no-version
/home/ec2-user/recon-ng/recon-cli -C "options set TIMEOUT 60" --no-version
sleep 10

# Put the seeded domains into the required table
for domain in $domains
do
	printf "$domain\n\n" | /home/ec2-user/recon-ng/recon-cli -w nbnco -C "db insert domains" --no-version
done
/home/ec2-user/recon-ng/recon-cli -w nbnco -C "show domains" --no-version

# Enumerate domains
/home/ec2-user/recon-ng/recon-cli -C "marketplace install brute_hosts" --no-version
/home/ec2-user/recon-ng/recon-cli -C "modules load brute_hosts" --no-version
for domain in $domains
do
	/home/ec2-user/recon-ng/recon-cli -w $PSCAN_RECONNG_WORKSPACE -m recon/domains-hosts/brute_hosts -c "options set SOURCE $domain" --no-version
	/home/ec2-user/recon-ng/recon-cli -w $PSCAN_RECONNG_WORKSPACE -m recon/domains-hosts/brute_hosts -c "run" --no-version
	sleep 10
done

/home/ec2-user/recon-ng/recon-cli -C "marketplace install hackertarget" --no-version
/home/ec2-user/recon-ng/recon-cli -C "modules load hackertarget" --no-version
for domain in $domains
do
	/home/ec2-user/recon-ng/recon-cli -w $PSCAN_RECONNG_WORKSPACE -m recon/domains-hosts/hackertarget -c "options set SOURCE $domain" --no-version
	/home/ec2-user/recon-ng/recon-cli -w $PSCAN_RECONNG_WORKSPACE -m recon/domains-hosts/hackertarget -c "run" --no-version
	sleep 10
done

/home/ec2-user/recon-ng/recon-cli -C "marketplace install certificate_transparency" --no-version
/home/ec2-user/recon-ng/recon-cli -C "modules load certificate_transparency" --no-version
for domain in $domains
do
	/home/ec2-user/recon-ng/recon-cli -w $PSCAN_RECONNG_WORKSPACE -m recon/domains-hosts/certificate_transparency -c "options set SOURCE $domain" --no-version
	/home/ec2-user/recon-ng/recon-cli -w $PSCAN_RECONNG_WORKSPACE -m recon/domains-hosts/certificate_transparency -c "run" --no-version
	sleep 10
done

/home/ec2-user/recon-ng/recon-cli -C "marketplace install bing_domain_web" --no-version
/home/ec2-user/recon-ng/recon-cli -C "modules load bing_domain_web" --no-version
for domain in $domains
do
	/home/ec2-user/recon-ng/recon-cli -w $PSCAN_RECONNG_WORKSPACE -m recon/domains-hosts/bing_domain_web -c "options set SOURCE $domain" --no-version
	/home/ec2-user/recon-ng/recon-cli -w $PSCAN_RECONNG_WORKSPACE -m recon/domains-hosts/bing_domain_web -c "run" --no-version
	sleep 10
done

/home/ec2-user/recon-ng/recon-cli -C "marketplace install google_site_web" --no-version
/home/ec2-user/recon-ng/recon-cli -C "modules load google_site_web" --no-version
for domain in $domains
do
	/home/ec2-user/recon-ng/recon-cli -w $PSCAN_RECONNG_WORKSPACE -m recon/domains-hosts/google_site_web -c "options set SOURCE $domain" --no-version
	/home/ec2-user/recon-ng/recon-cli -w $PSCAN_RECONNG_WORKSPACE -m recon/domains-hosts/google_site_web -c "run" --no-version
	sleep 10
done

# Forward-resolve everything
/home/ec2-user/recon-ng/recon-cli -C "marketplace install recon/hosts-hosts/resolve" --no-version
/home/ec2-user/recon-ng/recon-cli -C "modules load resolve" --no-version
/home/ec2-user/recon-ng/recon-cli -w $PSCAN_RECONNG_WORKSPACE -m recon/hosts-hosts/resolve -c "run" --no-version

# Export to csv
/home/ec2-user/recon-ng/recon-cli -C "marketplace install csv" --no-version
/home/ec2-user/recon-ng/recon-cli -C "modules load reporting/csv" --no-version
/home/ec2-user/recon-ng/recon-cli -w $PSCAN_RECONNG_WORKSPACE -m reporting/csv -c "options set HEADERS True" --no-version
/home/ec2-user/recon-ng/recon-cli -w $PSCAN_RECONNG_WORKSPACE -m reporting/csv -c "run" --no-version

aws s3 cp /home/ec2-user/.recon-ng/workspaces/$PSCAN_RECONNG_WORKSPACE/results.csv s3://$PSCAN_S3_BUCKET
rm /home/ec2-user/.recon-ng/workspaces/$PSCAN_RECONNG_WORKSPACE/results.csv

# All done. Wait a nominal period, and then stop the instance.
sleep 60
TOKEN=`curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"`
INSTANCE_ID=$(curl http://169.254.169.254/latest/meta-data/instance-id -H "X-aws-ec2-metadata-token: $TOKEN")
aws ec2 stop-instances --instance-ids $INSTANCE_ID --region ap-southeast-2

