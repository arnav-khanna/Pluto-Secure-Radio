# Pluto Secure Radio

Secure, low-latency packet radio for paired ADALM-Pluto SDRs. The active
protocol is V2 only: compact binary frames, optional payload compression,
X25519/AES-256-GCM confidentiality, encrypted Ed25519 sender signatures, and
a dedicated fast ACK waveform with bounded retransmissions.

## Status

This is a two-node direct-link implementation. It does not currently relay or
route through intermediate nodes; `TTL` and hop fields are authenticated
private metadata for future mesh work.

## Documentation

- [Current packet reference](CURRENT_DATA_PACKET.md) — exact on-air layout,
  visible fields, encryption, signing, compression, ACK behavior.
- [V2 architecture](V2_ARCHITECTURE.md) — implementation and protocol details.
- [Contributing guide](CONTRIBUTING.md) — development and test expectations.
- [Security policy](SECURITY.md) — key handling and vulnerability reporting.
- [Code of conduct](CODE_OF_CONDUCT.md) — collaboration and safety standards.
- [Changelog](CHANGELOG.md) — user-visible protocol changes.

## Run

Start the receiver on the destination Pluto:

```bash
PYTHONPATH=. ./.venv/bin/python -m pluto_json_radio.rx \
  --config configs/pluto.example.yaml
```

Send a message from the source Pluto:

```bash
PYTHONPATH=. ./.venv/bin/python -m pluto_json_radio.tx \
  --config configs/pluto.example.yaml \
  --text "hello"
```

Build and inspect a frame without using a Pluto:

```bash
PYTHONPATH=. ./.venv/bin/python -m pluto_json_radio.tx \
  --config configs/pluto.example.yaml \
  --text "radio test" --dry-run
```

## Configuration and keys

Create the local active configuration from the safe template:

```bash
cp configs/pluto.example.yaml.template configs/pluto.example.yaml
```

Each standalone folder has its own active configuration. The folders must use
matching PHY and protocol settings. Their Pluto URI, local node role, and
private keys intentionally differ. The active file is intentionally ignored by
Git.

Generate replacement key pairs with:

```bash
PYTHONPATH=. ./.venv/bin/python -m pluto_json_radio.keys --kind all
```

Keep `private_key` and `signing_private_key` on their owning node. Exchange
only public keys and place them in the peer-public-key maps. Restart receivers
after a key change.

## Verify

```bash
PYTHONPATH=. ./.venv/bin/pytest -q
```

The test suite verifies encrypted V2 encode/decode, hidden metadata, sender
signature rejection on tampering, 2-FSK recovery, and fast ACK recovery.

## Project layout

```text
pluto_json_radio/
  tx.py       sender, retransmission, ACK matching
  rx.py       continuous receiver, verification, ACK transmission
  v2.py       confidential binary packet codec
  phy.py      2-FSK modem and fast ACK waveform
  pluto.py    ADALM-Pluto runtime integration
  keys.py     X25519 and Ed25519 key generator
configs/      node-specific Pluto and key configuration
tests/        V2 protocol and PHY tests
```

## Compatibility

Both peers must run the same V2 wire layout. Update and restart both folders
together when changing protocol code or cryptographic key configuration.
