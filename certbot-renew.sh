#!/bin/sh

while true; do
    certbot renew --nginx --quiet
    sleep 12h  # Check for renewal twice a day
done 