#!/bin/sh
# Debian Bookworm packages from signed APT repositories with deterministic mirror fallback.
set -eu
[ "$#" -gt 0 ] || { echo "Pass package names" >&2; exit 2; }
primary="${APT_PRIMARY_DEBIAN_URL:-https://mirror.metanet.ch/debian}"
primary_security="${APT_PRIMARY_SECURITY_URL:-https://mirror.metanet.ch/debian-security}"
fallback="${APT_FALLBACK_DEBIAN_URL:-https://mirrors.huaweicloud.com/repository/debian}"
fallback_security="${APT_FALLBACK_SECURITY_URL:-https://mirrors.huaweicloud.com/repository/debian-security}"
for url in "$primary" "$primary_security" "$fallback" "$fallback_security"; do
  case "$url" in https://*) ;; *) echo "APT mirror must use HTTPS" >&2; exit 2;; esac
done
keyring=/usr/share/keyrings/debian-archive-keyring.gpg
[ -f "$keyring" ] || { echo "Debian archive keyring missing" >&2; exit 1; }
sources=/etc/apt/sources.list.d/debian.sources
attempt() {
  main="$1"; security="$2"; shift 2
  rm -f /etc/apt/sources.list
  cat > "$sources" <<EOF
Types: deb
URIs: $main
Suites: bookworm bookworm-updates
Components: main
Signed-By: $keyring

Types: deb
URIs: $security
Suites: bookworm-security
Components: main
Signed-By: $keyring
EOF
  rm -rf /var/lib/apt/lists/*
  mkdir -p /var/lib/apt/lists/partial
  apt-get -o APT::Update::Error-Mode=any -o Acquire::Retries=1 -o Acquire::https::Timeout=25 update || return 1
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends -o Acquire::Retries=1 -o Acquire::https::Timeout=25 "$@" || return 1
}
if attempt "$primary" "$primary_security" "$@"; then
  echo "APT primary mirror succeeded"
elif attempt "$fallback" "$fallback_security" "$@"; then
  echo "APT fallback mirror succeeded"
else
  echo "Both Debian APT mirrors failed" >&2
  exit 1
fi
rm -rf /var/lib/apt/lists/*
