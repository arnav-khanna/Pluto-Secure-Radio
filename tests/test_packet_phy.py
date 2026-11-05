import base64
import zlib

import pytest

from pluto_json_radio.keys import generate_ed25519_keypair, generate_x25519_keypair
from pluto_json_radio.phy import (
    find_fast_acknowledgements,
    find_packets,
    modulate_fast_acknowledgement,
    modulate_packet,
)
from pluto_json_radio.v2 import V2Error, decode_v2_payload, encode_v2_frame, v2_application


def _key_material() -> tuple[dict[str, str], dict[str, object]]:
    sender_encryption = generate_x25519_keypair()
    receiver_encryption = generate_x25519_keypair()
    sender_signing = generate_ed25519_keypair()
    return (
        {
            "encryption_method": "x25519-aesgcm",
            "private_key": sender_encryption["private_key"],
            "recipient_public_key": receiver_encryption["public_key"],
            "signing_private_key": sender_signing["private_key"],
        },
        {
            "private_key": receiver_encryption["private_key"],
            "peer_public_keys_by_code": {2: sender_encryption["public_key"]},
            "peer_signing_public_keys_by_code": {2: sender_signing["public_key"]},
        },
    )


def test_secure_v2_frame_round_trip_and_hidden_shell():
    send, receive = _key_material()
    frame, display = encode_v2_frame(
        receiver_code=1, source_code=2, nonce="0123456789abcdef",
        payload={"text": "private", "seq": 7}, compression_method="none", **send,
    )
    shell = decode_v2_payload(frame[2:])
    assert set(shell) == {"_wire_format", "_encrypted", "_signed", "receiver_node_id", "nonce"}
    decoded = decode_v2_payload(frame[2:], **receive)
    assert decoded["payload"] == {"text": "private", "seq": 7}
    assert decoded["signature_method"] == "ed25519"
    assert v2_application(decoded, {1: "mac-a", 2: "mac-b"})["sender_address"] == "mac-b"
    assert display["sender_signature"] == decoded["sender_signature"]


def test_signature_tamper_is_rejected_even_with_new_crc():
    send, receive = _key_material()
    frame, _ = encode_v2_frame(
        receiver_code=1, source_code=2, nonce="fedcba9876543210",
        payload={"text": "protected"}, compression_method="none", **send,
    )
    tampered = bytearray(frame[2:])
    tampered[-5] ^= 1
    tampered[-4:] = zlib.crc32(tampered[:-4]).to_bytes(4, "big")
    with pytest.raises(V2Error, match="authenticated decryption"):
        decode_v2_payload(bytes(tampered), **receive)


def test_v2_modem_and_fast_ack_round_trips():
    send, receive = _key_material()
    preamble = bytes.fromhex("5555555555555555d391ac6f")
    frame, _ = encode_v2_frame(
        receiver_code=1, source_code=2, nonce="0011223344556677",
        payload={"text": "radio"}, compression_method="none", **send,
    )
    iq = modulate_packet(frame, preamble=preamble, sample_rate_hz=2_000_000, samples_per_symbol=8, tone_deviation_hz=125_000)
    packet = find_packets(iq, preamble=preamble, sample_rate_hz=2_000_000, samples_per_symbol=8, tone_deviation_hz=125_000, max_payload_bytes=512)[0]
    assert decode_v2_payload(packet.packet.payload_bytes, **receive)["payload"]["text"] == "radio"
    ack_iq = modulate_fast_acknowledgement("0011223344556677", preamble=preamble, sample_rate_hz=2_000_000, samples_per_symbol=8, tone_deviation_hz=125_000)
    assert "0011223344556677" in find_fast_acknowledgements(ack_iq, preamble=preamble, sample_rate_hz=2_000_000, samples_per_symbol=8, tone_deviation_hz=125_000)


def test_key_generators_return_raw_32_byte_keys():
    for pair in (generate_x25519_keypair(), generate_ed25519_keypair()):
        assert len(base64.b64decode(pair["private_key"], validate=True)) == 32
        assert len(base64.b64decode(pair["public_key"], validate=True)) == 32
