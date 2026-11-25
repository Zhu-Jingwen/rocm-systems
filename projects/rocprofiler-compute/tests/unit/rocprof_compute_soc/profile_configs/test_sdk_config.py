# Copyright (c) Advanced Micro Devices, Inc.
# SPDX-License-Identifier:  MIT
"""Check the gfx1201 SDK configuration against pinned external contracts."""

import re
from pathlib import Path
from typing import Any

import pytest

from vendored import yaml

# Reference: https://github.com/ROCm/rocm-systems/blob/e92aa6ee8c01f991c9da08ea386330a6374e0f4a/projects/rocprofiler-sdk/source/share/rocprofiler-sdk/config.yaml
HISTORICAL = {
    "CU_NUM": {
        "expression": "simd_count/simd_per_cu",
    },
    "FETCH_SIZE": {
        "expression": (
            "(GL2C_EA_RDREQ_32B_sum*32+GL2C_EA_RDREQ_64B_sum*64+GL2C_EA"
            "_RDREQ_128B_sum*128+GL2C_EA_RDREQ_256B_sum*256)/1024"
        ),
    },
    "FetchSize": {
        "expression": "FETCH_SIZE",
    },
    "GL2C_EA_RDREQ": {
        "block": "GL2C",
        "event": 140,
    },
    "GL2C_EA_RDREQ_128B": {
        "block": "GL2C",
        "event": 148,
    },
    "GL2C_EA_RDREQ_128B_sum": {
        "expression": "reduce(GL2C_EA_RDREQ_128B,sum)",
    },
    "GL2C_EA_RDREQ_256B": {
        "block": "GL2C",
        "event": 149,
    },
    "GL2C_EA_RDREQ_256B_sum": {
        "expression": "reduce(GL2C_EA_RDREQ_256B,sum)",
    },
    "GL2C_EA_RDREQ_32B": {
        "block": "GL2C",
        "event": 146,
    },
    "GL2C_EA_RDREQ_32B_sum": {
        "expression": "reduce(GL2C_EA_RDREQ_32B,sum)",
    },
    "GL2C_EA_RDREQ_64B": {
        "block": "GL2C",
        "event": 147,
    },
    "GL2C_EA_RDREQ_64B_sum": {
        "expression": "reduce(GL2C_EA_RDREQ_64B,sum)",
    },
    "GL2C_EA_RDREQ_sum": {
        "expression": "reduce(GL2C_EA_RDREQ,sum)",
    },
    "GL2C_EA_WRREQ": {
        "block": "GL2C",
        "event": 108,
    },
    "GL2C_EA_WRREQ_64B": {
        "block": "GL2C",
        "event": 114,
    },
    "GL2C_EA_WRREQ_64B_sum": {
        "expression": "reduce(GL2C_EA_WRREQ_64B,sum)",
    },
    "GL2C_EA_WRREQ_STALL": {
        "block": "GL2C",
        "event": 122,
    },
    "GL2C_EA_WRREQ_STALL_max": {
        "expression": "reduce(GL2C_EA_WRREQ_STALL,max)",
    },
    "GL2C_EA_WRREQ_sum": {
        "expression": "reduce(GL2C_EA_WRREQ,sum)",
    },
    "GL2C_HIT": {
        "block": "GL2C",
        "event": 41,
    },
    "GL2C_HIT_sum": {
        "expression": "reduce(GL2C_HIT,sum)",
    },
    "GL2C_MC_WRREQ_STALL": {
        "block": "GL2C",
        "event": 122,
    },
    "GL2C_MISS": {
        "block": "GL2C",
        "event": 42,
    },
    "GL2C_MISS_sum": {
        "expression": "reduce(GL2C_MISS,sum)",
    },
    "GL2C_WRREQ_STALL_max": {
        "expression": "reduce(GL2C_MC_WRREQ_STALL,max)",
    },
    "GPUBusy": {
        "expression": "100*reduce(GRBM_GUI_ACTIVE,max)/reduce(GRBM_COUNT,max)",
    },
    "GPU_UTIL": {
        "expression": "100*reduce(GRBM_GUI_ACTIVE,max)/reduce(GRBM_COUNT,max)",
    },
    "GRBM_COUNT": {
        "block": "GRBM",
        "event": 0,
    },
    "GRBM_GUI_ACTIVE": {
        "block": "GRBM",
        "event": 2,
    },
    "L0CacheHit": {
        "expression": "(1-(reduce(TCP_REQ_MISS,sum)/reduce(TCP_REQ,sum)))*100",
    },
    "L2CacheHit": {
        "expression": (
            "100*reduce(GL2C_HIT,sum)/(reduce(GL2C_HIT,sum)+reduce(GL2C_MISS,sum))"
        ),
    },
    "LDSBankConflict": {
        "expression": (
            "100*reduce(SQC_LDS_BANK_CONFLICT,sum)/reduce(SQC_LDS_IDX_ACTIVE,sum)"
        ),
    },
    "LdsUtil": {
        "expression": (
            "100*reduce(SQC_LDS_IDX_ACTIVE,sum)/(reduce(GRBM_GUI_ACTIVE"
            ",max)*(SIMD_NUM/4))"
        ),
    },
    "MeanOccupancyPerActiveCU": {
        "expression": "reduce(SQ_WAVE_CYCLES,sum)/reduce(SQ_BUSY_CYCLES,sum)",
    },
    "MeanOccupancyPerCU": {
        "expression": ("reduce(SQ_WAVE_CYCLES,sum)/reduce(GRBM_GUI_ACTIVE,max)/CU_NUM"),
    },
    "MemUnitBusy": {
        "expression": "100*reduce(TA_TA_BUSY,max)/reduce(GRBM_GUI_ACTIVE,max)",
    },
    "OccupancyPercent": {
        "expression": (
            "100*reduce(SQ_WAVE_CYCLES,sum)/reduce(GRBM_GUI_ACTIVE,max)/CU_NUM/32"
        ),
    },
    "SALUInsts": {
        "expression": "reduce(SQ_INSTS_SALU,sum)/reduce(SQ_WAVES,sum)",
    },
    "SE_NUM": {
        "expression": "array_count/simd_arrays_per_engine",
    },
    "SFetchInsts": {
        "expression": "reduce(SQ_INSTS_SMEM,sum)/reduce(SQ_WAVES,sum)",
    },
    "SIMD_NUM": {
        "expression": "simd_count",
    },
    "SIMD_UTILIZATION": {
        "expression": (
            "reduce(SQ_BUSY_CYCLES,sum)/reduce(GRBM_COUNT,max)/(SIMD_NUM/4)"
        ),
    },
    "SQC_ICACHE_HITS": {
        "block": "SQ",
        "event": 302,
    },
    "SQC_ICACHE_MISSES": {
        "block": "SQ",
        "event": 303,
    },
    "SQC_ICACHE_REQ": {
        "block": "SQ",
        "event": 301,
    },
    "SQC_LDS_BANK_CONFLICT": {
        "block": "SQ",
        "event": 288,
    },
    "SQC_LDS_IDX_ACTIVE": {
        "block": "SQ",
        "event": 293,
    },
    "SQ_ACCUM_PREV": {
        "block": "SQ",
        "event": 1,
    },
    "SQ_BUSY_CYCLES": {
        "block": "SQ",
        "event": 3,
    },
    "SQ_INSTS_FLAT": {
        "block": "SQ",
        "event": 44,
    },
    "SQ_INSTS_LDS": {
        "block": "SQ",
        "event": 45,
    },
    "SQ_INSTS_SALU": {
        "block": "SQ",
        "event": 46,
    },
    "SQ_INSTS_SMEM": {
        "block": "SQ",
        "event": 47,
    },
    "SQ_INSTS_TEX_LOAD": {
        "block": "SQ",
        "event": 54,
    },
    "SQ_INSTS_TEX_STORE": {
        "block": "SQ",
        "event": 55,
    },
    "SQ_INSTS_VALU": {
        "block": "SQ",
        "event": 50,
    },
    "SQ_INSTS_VEC32_LEVEL_LDS": {
        "block": "SQ",
        "event": 250,
    },
    "SQ_INSTS_WAVE32": {
        "block": "SQ",
        "event": 58,
    },
    "SQ_INSTS_WAVE32_LDS": {
        "block": "SQ",
        "event": 60,
    },
    "SQ_INSTS_WAVE32_VALU": {
        "block": "SQ",
        "event": 61,
    },
    "SQ_INST_CYCLES_VALU": {
        "block": "SQ",
        "event": 99,
    },
    "SQ_INST_CYCLES_VMEM": {
        "block": "SQ",
        "event": 102,
    },
    "SQ_INST_LEVEL_LDS": {
        "block": "SQ",
        "event": 75,
    },
    "SQ_WAIT_ANY": {
        "block": "SQ",
        "event": 27,
    },
    "SQ_WAIT_INST_ANY": {
        "block": "SQ",
        "event": 26,
    },
    "SQ_WAVE32_INSTS": {
        "block": "SQ",
        "event": 70,
    },
    "SQ_WAVE64_INSTS": {
        "block": "SQ",
        "event": 71,
    },
    "SQ_WAVES": {
        "block": "SQ",
        "event": 4,
    },
    "SQ_WAVES_sum": {
        "expression": "reduce(SQ_WAVES,sum)",
    },
    "SQ_WAVE_CYCLES": {
        "block": "SQ",
        "event": 24,
    },
    "TA_BUFFER_LOAD_WAVEFRONTS": {
        "block": "TA",
        "event": 45,
    },
    "TA_BUFFER_LOAD_WAVEFRONTS_sum": {
        "expression": "reduce(TA_BUFFER_LOAD_WAVEFRONTS,sum)",
    },
    "TA_BUFFER_STORE_WAVEFRONTS": {
        "block": "TA",
        "event": 46,
    },
    "TA_BUFFER_STORE_WAVEFRONTS_sum": {
        "expression": "reduce(TA_BUFFER_STORE_WAVEFRONTS,sum)",
    },
    "TA_BUSY_avr": {
        "expression": "reduce(TA_TA_BUSY,avr)",
    },
    "TA_BUSY_max": {
        "expression": "reduce(TA_TA_BUSY,max)",
    },
    "TA_BUSY_min": {
        "expression": "reduce(TA_TA_BUSY,min)",
    },
    "TA_TA_BUSY": {
        "block": "TA",
        "event": 15,
    },
    "TCP_REQ": {
        "block": "TCP",
        "event": 9,
    },
    "TCP_REQ_MISS": {
        "block": "TCP",
        "event": 17,
    },
    "VALUBusy": {
        "expression": (
            "100*reduce(SQ_INST_CYCLES_VALU,sum)/(SIMD_NUM/4)/reduce(GR"
            "BM_GUI_ACTIVE,max)"
        ),
    },
    "VALUInsts": {
        "expression": "reduce(SQ_INSTS_VALU,sum)/reduce(SQ_WAVES,sum)",
    },
    "ValuPipeIssueUtil": {
        "expression": (
            "100*reduce(SQ_INST_CYCLES_VALU,sum)/(reduce(GRBM_GUI_ACTIV"
            "E,max)*(SIMD_NUM/4))"
        ),
    },
    "WAVE_DEP_WAIT": {
        "expression": "100*reduce(SQ_WAIT_ANY,sum)/reduce(SQ_WAVE_CYCLES,sum)",
    },
    "WAVE_ISSUE_WAIT": {
        "expression": ("100*reduce(SQ_WAIT_INST_ANY,sum)/reduce(SQ_WAVE_CYCLES,sum)"),
    },
    "Wavefronts": {
        "expression": "reduce(SQ_WAVES,sum)",
    },
    "WriteUnitStalled": {
        "expression": "100*GL2C_WRREQ_STALL_max/reduce(GRBM_GUI_ACTIVE,max)",
    },
}

ADDITIONAL = {
    "GL1C_BUSY": {
        "block": "GL1C",
        "event": 1,
    },
    "GL1C_BUSY_sum": {
        "expression": "reduce(GL1C_BUSY,sum)",
    },
    "GL1C_CYCLE": {
        "block": "GL1C",
        "event": 0,
    },
    "GL1C_CYCLE_sum": {
        "expression": "reduce(GL1C_CYCLE,sum)",
    },
    "GL1C_GL2_REQ_READ_64B": {
        "block": "GL1C",
        "event": 9,
    },
    "GL1C_GL2_REQ_READ_64B_sum": {
        "expression": "reduce(GL1C_GL2_REQ_READ_64B,sum)",
    },
    "GL1C_REQ_READ_128B": {
        "block": "GL1C",
        "event": 38,
    },
    "GL1C_REQ_READ_128B_sum": {
        "expression": "reduce(GL1C_REQ_READ_128B,sum)",
    },
    "GL1C_REQ_READ_32B": {
        "block": "GL1C",
        "event": 36,
    },
    "GL1C_REQ_READ_32B_sum": {
        "expression": "reduce(GL1C_REQ_READ_32B,sum)",
    },
    "GL1C_REQ_WRITE_32B": {
        "block": "GL1C",
        "event": 42,
    },
    "GL1C_REQ_WRITE_32B_sum": {
        "expression": "reduce(GL1C_REQ_WRITE_32B,sum)",
    },
    "GL2C_BUSY": {
        "block": "GL2C",
        "event": 2,
    },
    "GL2C_BUSY_sum": {
        "expression": "reduce(GL2C_BUSY,sum)",
    },
    "GL2C_CYCLE": {
        "block": "GL2C",
        "event": 1,
    },
    "GL2C_CYCLE_sum": {
        "expression": "reduce(GL2C_CYCLE,sum)",
    },
    "GL2C_READ_128_REQ": {
        "block": "GL2C",
        "event": 80,
    },
    "GL2C_READ_128_REQ_sum": {
        "expression": "reduce(GL2C_READ_128_REQ,sum)",
    },
    "GL2C_READ_32_REQ": {
        "block": "GL2C",
        "event": 78,
    },
    "GL2C_READ_32_REQ_sum": {
        "expression": "reduce(GL2C_READ_32_REQ,sum)",
    },
    "GL2C_READ_64_REQ": {
        "block": "GL2C",
        "event": 79,
    },
    "GL2C_READ_64_REQ_sum": {
        "expression": "reduce(GL2C_READ_64_REQ,sum)",
    },
    "SQC_DCACHE_DUPLICATE_MISSES": {
        "block": "SQ",
        "event": 328,
    },
    "SQC_DCACHE_DUPLICATE_MISSES_sum": {
        "expression": "reduce(SQC_DCACHE_DUPLICATE_MISSES,sum)",
    },
    "SQC_DCACHE_MISSES": {
        "block": "SQ",
        "event": 327,
    },
    "SQC_DCACHE_MISSES_sum": {
        "expression": "reduce(SQC_DCACHE_MISSES,sum)",
    },
    "SQC_TC_INST_REQ": {
        "block": "SQ",
        "event": 315,
    },
    "SQC_TC_INST_REQ_sum": {
        "expression": "reduce(SQC_TC_INST_REQ,sum)",
    },
    "TCP_REQ_READ": {
        "block": "TCP",
        "event": 10,
    },
    "TCP_REQ_READ_sum": {
        "expression": "reduce(TCP_REQ_READ,sum)",
    },
    "TCP_REQ_WRITE": {
        "block": "TCP",
        "event": 14,
    },
    "TCP_REQ_WRITE_sum": {
        "expression": "reduce(TCP_REQ_WRITE,sum)",
    },
}


@pytest.fixture(scope="module")
def definitions() -> dict[str, list[dict[str, Any]]]:
    project = Path(__file__).resolve().parents[4]
    candidates = [
        project / "src/rocprof_compute_soc/profile_configs/sdk_config.yaml",
        project / "rocprof_compute_soc/profile_configs/sdk_config.yaml",
    ]
    path = next(candidate for candidate in candidates if candidate.exists())
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    selected: dict[str, list[dict[str, Any]]] = {}
    for entry in config["rocprofiler-sdk"]["counters"]:
        for definition in entry["definitions"]:
            if "gfx1201" in definition["architectures"]:
                selected.setdefault(entry["name"], []).append(definition)
    return selected


@pytest.mark.parametrize("name,expected", sorted(HISTORICAL.items()))
def test_historical_definition(definitions, name, expected):
    assert len(definitions[name]) == 1
    actual = {
        key: value
        for key, value in definitions[name][0].items()
        if key != "architectures"
    }
    assert actual == expected


def test_unique_architecture_definitions(definitions):
    assert all(len(items) == 1 for items in definitions.values())


def test_historical_expression_dependencies(definitions):
    language = {
        "reduce",
        "sum",
        "max",
        "min",
        "avr",
        "simd_count",
        "simd_per_cu",
        "array_count",
        "simd_arrays_per_engine",
    }
    for name, definition in HISTORICAL.items():
        references = set(
            re.findall(r"\b[A-Za-z_]\w*\b", definition.get("expression", ""))
        )
        assert references <= definitions.keys() | language, name


@pytest.mark.parametrize("name,expected", sorted(ADDITIONAL.items()))
def test_additional_definition(definitions, name, expected):
    assert len(definitions[name]) == 1
    actual = {
        key: value
        for key, value in definitions[name][0].items()
        if key != "architectures"
    }
    assert actual == expected
