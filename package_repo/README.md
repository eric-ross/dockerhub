# Vancouver package repo

## Sites

This contains the following servers:

- pypi: HP internal python packages.
- rpms: HP internal rpm packages for RHEL.
- fwstaging-int: The inside the firewall staging server.  It is used for uploading images and providing updates to products that don't have access to the internet.

## Procedure

-  Install docker.io and docker-compose on an Ubuntu 16 system.
-  Give this server the names rpms, fwstaging-int and pypi.  The servers will match name.* so any subdomain/domain is OK.  Add these names to the appropriate DNS.
-  For now there is no dockerhub registry in HP.  So the base package package_repo must be built manually using package_repo/build.sh
-  Run the full stack:  docker-compose up
-  Shutdown:  docker-compose stop
-  Remove images:  docker-compose rm

