# Changelog

This project follows the spirit of [Keep a Changelog](https://keepachangelog.com/)
and semantic versioning for wire-compatible releases.

## [Unreleased]

### Changed

- Removed V1 JSON framing, legacy fallback code, installer helpers, and
  downloaded setup artifacts.
- Simplified the application to the active V2 secure packet path and fast ACK.

## [2.0.0]

### Added

- Binary typed payload codec with dictionary field IDs and varints.
- X25519/HKDF/AES-256-GCM encrypted data frames.
- Encrypted Ed25519 sender signatures.
- Continuous low-latency receiver and fixed fast ACK waveform.
- Adaptive payload compression and bounded retransmissions.
