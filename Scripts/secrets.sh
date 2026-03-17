#!/usr/bin/env bash
set -e
mkdir -p ./Secrets
# ENV VARS
: "${POSTGRES_PASSWORD:?Environment variable POSTGRES_PASSWOR is required}"
: "${FERNET_PASSWORD:?Environment variable FERNET_PASSWORD is required}"

# FILES 
if [ ! -f ../.env ]; then
  echo "Please change default values from .env"
  echo "WARN -> Default values are public and well known."
  cp ../Secrets_Template/env_example ../.env
  echo "Copied the example .env to ./Secrets/.env"
fi

if [ ! -f ../Secrets/users.toml ]; then
  echo "Please change default values from users.toml in ./Secrets."
  echo "WARN -> Default values are public and well known."
  cp ../Secrets_Template/users.toml ../Secrets
  echo "Copied the example users.toml to ./Secrets/users.toml"
fi

if [ ! -f ../Secrets/cert.key ]; then
  echo "Generating random TESTING CERTIFICATE."
  echo "This certificate is not validated by external certification authorities and will make the app be flagged as suspicious to users."
  echo "WARM -> OBTAIN A REAL CERTIFICATE AND REPLACE THE ONES IN ./Secrets/"
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ../Secrets/cert.key \
  -out ../Secrets/cert.crt \
  -subj "/C=CO/ST=Bogotá DC/L=Bogotá/O=Dev/CN=Localhost"
  echo "Created DEVELOPMENT certificates for HTTPS."
fi

if [ ! -f ../Secrets/jwt_private.pem ]; then
  echo "Creating a pair of private an public keys for salting the tokens used by authentication."
  echo "WARN -> STORE THOSE FILES SECURELY."
  openssl genpkey -algorithm ED25519 \
    -out ../Secrets/jwt_private.pem
  openssl pkey -in ../Secrets/jwt_private.pem \
    -pubout -out ../Secrets/jwt_public.pem
  echo "Created certificates for tokens."
fi

echo "Secret generator done!"
