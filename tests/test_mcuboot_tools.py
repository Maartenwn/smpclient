"""Test the FW image inspection tools."""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Protocol

import pytest

from smpclient.mcuboot import (
    IMAGE_MAGIC,
    IMAGE_TLV,
    IMAGE_TLV_INFO_MAGIC,
    ImageHeader,
    ImageInfo,
    ImageVersion,
)


class _ImageFileFixture(Protocol):
    PATH: Path
    SHA256: bytes
    KEYHASH: bytes
    RSA2048_PSS: bytes


class _HELLO_WORLD_SIGNED_BASE:
    SHA256 = bytes.fromhex("90a0d88baaa733640dab01fd8e9311dbe8ea1032966b6b286ef6ef772cc608cf")
    KEYHASH = bytes.fromhex("fc5701dc6135e1323847bdc40f04d2e5bee5833b23c29f93593d00018cfa9994")


class SIGNED_BIN(_HELLO_WORLD_SIGNED_BASE):
    PATH = Path("tests", "fixtures", "zephyr-v3.5.0-2795-g28ff83515d", "hello_world.signed.bin")
    RSA2048_PSS = bytes.fromhex(
        "457dde4937c30fc253fc98c241defb2c2d8f50a7cd74d9166629c5498fcaa822210bccfd6468ae9846a8a52fa0eaa647d9b5ffdcaea4fb397ce2a0e5912a4933fe6945ec65ddf826496cde2fd0530ff105ce37405e7bc60d6b52ee01f317a1219db3d49e48be9798095254d135d55b832bbe60780b9bf61f95fb83b1131ae576dd33945895bd0a8c870c425342449d211155fa87b134c2c3164319c46827106c27c67c9f7418877aab48164aaf567b2c21964a26735f5746400198ae1fd94f2f56f26eebbd38e3e3d4c36f6c764f9ee4639cf99adaced9d38966fc0879f3005d697e3b588b71b6bb08a466384080353ead7c3b1fb8eed51af6497ef1f1d836be"  # noqa
    )


class SIGNED_HEX(_HELLO_WORLD_SIGNED_BASE):
    PATH = Path("tests", "fixtures", "zephyr-v3.5.0-2795-g28ff83515d", "hello_world.signed.hex")
    RSA2048_PSS = bytes.fromhex(
        "46d0c082b77b48a70af315db284beaf4cedae49a51f1aa935df934a2e14a6762773c43c926809cf0bd83b2e944c06d2666617083cdc7afbd358070e207759a6100997602e63313c2d3dcd68f7d8c04ab381751f3d96e7908076fee25b157c9d5922ddd2007c1a2f9104d1196dc7d702ee64b27db710f043d80c3e371e84682c0de402b7e3447a34900c71da3ba3bc7681c7cd28273b6e6f7c99bd731bd289d1710e0fbeb4619556ab0e4f343b09c394993e745acc450ef58589148d9daf8a63214d66ad09186503dd07a9c110f6c5cad2f3075838806c42c78c431454c947186e09f969f9564f1ba30771dc9df76985b2dbc47a7fe2bd2c2436b8c890b8e0de8"  # noqa
    )


@pytest.mark.parametrize("image", [SIGNED_BIN, SIGNED_HEX])
def test_ImageInfo(image: _ImageFileFixture) -> None:
    image_info = ImageInfo.load_file(str(image.PATH))

    assert image_info.file == str(image.PATH)

    # header
    h = image_info.header
    assert h.magic == IMAGE_MAGIC
    assert h.load_addr == 0
    assert h.hdr_size == 512
    assert h.protect_tlv_size == 0
    assert h.img_size == 24692
    assert h.flags == 0
    assert h.ver.major == 0
    assert h.ver.minor == 0
    assert h.ver.revision == 0
    assert h.ver.build_num == 0

    # TLV header
    t = image_info.tlv_info
    assert t.magic == IMAGE_TLV_INFO_MAGIC
    assert t.tlv_tot == 336

    # TLVs
    assert len(image_info.tlvs) == 3

    # IMAGE_TLV_SHA256
    v = image_info.get_tlv(IMAGE_TLV.SHA256)
    assert v.header.len == 32
    assert v.header.type == IMAGE_TLV.SHA256
    assert v.value == image.SHA256

    # IMAGE_TLV_KEYHASH
    v = image_info.get_tlv(IMAGE_TLV.KEYHASH)
    assert v.header.len == 32
    assert v.header.type == IMAGE_TLV.KEYHASH
    assert v.value == image.KEYHASH

    # IMAGE_TLV_RSA2048_PSS
    v = image_info.get_tlv(IMAGE_TLV.RSA2048_PSS)
    assert v.header.len == 256
    assert v.header.type == IMAGE_TLV.RSA2048_PSS
    assert v.value == image.RSA2048_PSS


@pytest.mark.parametrize("image", [SIGNED_BIN])
def test_ImageHeader(image: _ImageFileFixture) -> None:
    h = ImageHeader.load_file(str(image.PATH))

    assert h.magic == IMAGE_MAGIC
    assert h.load_addr == 0
    assert h.hdr_size == 512
    assert h.protect_tlv_size == 0
    assert h.img_size == 24692
    assert h.flags == 0
    assert h.ver.major == 0
    assert h.ver.minor == 0
    assert h.ver.revision == 0
    assert h.ver.build_num == 0


def test_ImageVersion() -> None:
    v = ImageVersion.loads(struct.pack("<BBHL", 1, 0xFF, 0xFFFF, 0xFFFFFFFF))
    assert v.major == 1
    assert v.minor == 0xFF
    assert v.revision == 0xFFFF
    assert v.build_num == 0xFFFFFFFF
    assert str(v) == "1.255.65535-build4294967295"
