# adds support for coordinate system work offsets
#
# Copyright (C) 2022-3  Andrew Mirsky <andrew@mirsky.net>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
#
#
import pickle, os
from extras.work_offsets import WorkOffsetsSupport
from extras.gcode_arcs import ArcSupport


class GrblSupport:

    def __init__(self, config):
        self.printer = config.get_printer()
        wo_config = config.getchoice('work_offsets',
                                     {'standard': 'standard', 'none': 'none'},
                                     default='standard')
        if wo_config == 'standard':
            self.work_offsets = WorkOffsetsSupport(config)
        arc_config = config.getboolean('arcs', default=True)
        gcode_arc_obj = self.printer.lookup_object('gcode_arc', None)
        if gcode_arc_obj and not arc_config:
            raise self.printer.config_error(
                "conflict: section `[gcode_arc]` included, but disabled in `[grbl]` section")
        if arc_config and not gcode_arc_obj:
            self.arc_commands = ArcSupport(config)


def load_config(config):
    return GrblSupport(config)
