#!/usr/bin/env python3
# -*- coding: utf8 -*-
# tab-width:4

# pylint: disable=useless-suppression             # [I0021]
# pylint: disable=missing-docstring               # [C0111] docstrings are always outdated and wrong
# pylint: disable=missing-param-doc               # [W9015]
# pylint: disable=missing-module-docstring        # [C0114]
# pylint: disable=fixme                           # [W0511] todo encouraged
# pylint: disable=line-too-long                   # [C0301]
# pylint: disable=too-many-instance-attributes    # [R0902]
# pylint: disable=too-many-lines                  # [C0302] too many lines in module
# pylint: disable=invalid-name                    # [C0103] single letter var names, name too descriptive
# pylint: disable=too-many-return-statements      # [R0911]
# pylint: disable=too-many-branches               # [R0912]
# pylint: disable=too-many-statements             # [R0915]
# pylint: disable=too-many-arguments              # [R0913]
# pylint: disable=too-many-nested-blocks          # [R1702]
# pylint: disable=too-many-locals                 # [R0914]
# pylint: disable=too-many-public-methods         # [R0904]
# pylint: disable=too-few-public-methods          # [R0903]
# pylint: disable=no-member                       # [E1101] no member for base
# pylint: disable=attribute-defined-outside-init  # [W0201]
# pylint: disable=too-many-boolean-expressions    # [R0916] in if statement

from __future__ import annotations

import logging
from pathlib import Path
from signal import SIG_DFL
from signal import SIGPIPE
from signal import signal

import click
import sh
from asserttool import gvd
from asserttool import ic
from asserttool import icp
from click_auto_help import AHGroup
from clicktool import click_add_options
from clicktool import click_global_options
from clicktool import tv
from eprint import eprint
from mounttool import block_special_path_is_mounted
from pathtool import path_is_block_special
from pathtool import wait_for_block_special_device_to_exist
from warntool import warn

logging.basicConfig(level=logging.INFO)
sh.mv = None  # use sh.busybox('mv'), coreutils ignores stdin read errors

# this should be earlier in the imports, but isort stops working
signal(SIGPIPE, SIG_DFL)


@click.group(no_args_is_help=True, cls=AHGroup)
@click_add_options(click_global_options)
@click.pass_context
def cli(
    ctx,
    verbose_inf: bool,
    dict_output: bool,
    verbose: bool = False,
) -> None:
    tty, verbose = tv(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
    )
    if not verbose:
        ic.disable()
    else:
        ic.enable()

    if verbose_inf:
        gvd.enable()


@cli.command()
@click.argument(
    "device",
    type=click.Path(
        exists=True,
        dir_okay=False,
        file_okay=True,
        allow_dash=False,
        path_type=Path,
    ),
    nargs=1,
    required=True,
)
@click.argument(
    "filesystem",
    type=click.Choice(
        [
            "fat16",
            "fat32",
            "ext4",
        ]
    ),
    nargs=1,
)
@click.option("--force", is_flag=True)
@click.option("--raw-device", is_flag=True)
@click_add_options(click_global_options)
@click.pass_context
def write(
    ctx,
    device: Path,
    filesystem: str,
    force: bool,
    raw_device: bool,
    verbose_inf: bool,
    dict_output: bool,
    verbose: bool = False,
) -> None:
    tty, verbose = tv(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
    )

    if not verbose:
        ic.disable()
    else:
        ic.enable()

    if verbose_inf:
        gvd.enable()
    if not raw_device:
        assert device.as_posix()[-1].isdigit()
    assert path_is_block_special(device)
    assert not block_special_path_is_mounted(
        device,
    )
    if not force:
        warn((device,))

    # this would introduce a devicetool dep...
    # wait_for_block_special_device_to_exist(device=device)
    if filesystem == "fat16":
        mkfs_command = sh.Command("mkfs.fat")
        mkfs_command = mkfs_command.bake("-F16", "-s2")
        mkfs_command = mkfs_command.bake(device.as_posix())

    elif filesystem == "fat32":
        mkfs_command = sh.Command("mkfs.fat")
        mkfs_command = mkfs_command.bake("-F32", "-s2")
        mkfs_command = mkfs_command.bake(device.as_posix())
    elif filesystem == "ext4":
        mkfs_command = sh.Command("mkfs.ext4")
        mkfs_command = mkfs_command.bake(device.as_posix())
    else:
        assert False
    wait_for_block_special_device_to_exist(device=device)
    result = mkfs_command()
    icp(result)
