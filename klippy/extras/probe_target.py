
from homing import HomingMove

# virtual mcu for probing a virtual endstop

# do we create this MCU once when the commands are registered?
# do we create it once we need it with the associated direction of the probing?
#    probably only want to create and register this "virtual" mcu once so there aren't many of them floating around each time the command is executed
#    if this is the case, we'll want to be able to move in xyz and therefore need to add all steppers as active ones
class ProbeMCU:
    def __init__(self, printer, pin_params):
        # Create an "endstop" object to handle the probe pin
        mcu = pin_params['chip']

        # what kind of object is this mcu endstop?
        self.mcu_endstop = mcu.setup_pin('endstop', pin_params)

        printer.register_event_handler('klippy:mcu_identify', self._handle_mcu_identify)

        # Wrappers
        self.get_mcu = self.mcu_endstop.get_mcu
        self.add_stepper = self.mcu_endstop.add_stepper
        self.get_steppers = self.mcu_endstop.get_steppers
        self.home_start = self.mcu_endstop.home_start
        self.home_wait = self.mcu_endstop.home_wait
        self.query_endstop = self.mcu_endstop.query_endstop

    # when this new "mcu" is identified, find the stepper and add it as if this mcu owned it
    def _handle_mcu_identify(self):
        kin = self.printer.lookup_object('toolhead').get_kinematics()
        for stepper in kin.get_steppers():
            if stepper.is_active_axis(self.axis):
                self.add_stepper(stepper)


class ProbeTarget:

    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        self.gcode.register_command('G38.2', self.cmd_ProbeTarget)

        # register virtual endstop
        self.probe_pin = self.printer.lookup_object('pins').register_chip('probe_target', self)

        ppins = self.printer.lookup_object('pins')
        pin = config.get('pin')
        pin_params = ppins.lookup_pin(pin, can_invert=True, can_pullup=True)
        self.probe_mcu = ProbeMCU(pin_params)

    def _handle_mcu_identify(self):
        print("new mcu identified as probing mcu")

    def cmd_ProbeTarget(self, cmd):
        # get probe direction and max travel distance
        direction = None
        max_travel = None

        # get probe feed rate
        feed_rate = None

        # get probe radius
        probe_radius = None

        # move probe
        position = self._probe(direction, max_travel, feed_rate)

        pass

    def _probe(self, direction, max_travel, speed):
        toolhead = self.printer.lookup_object('toolhead')
        # curtime = self.printer.get_reactor().monotonic()
        # phoming = self.printer.lookup_object('homing')
        pos = toolhead.get_position()

        probe_mcu = ProbeMCU()
        endstops = [(probe_mcu, "probe_target")]
        hmove = HomingMove(self.printer, endstops)

        try:
            epos = hmove.homing_move(pos, speed, probe_pos=True)
        except self.printer.command_error:
            if self.printer.is_shutdown():
                raise self.printer.command_error(
                    "Probing failed due to printer shutdown")
            raise
        if hmove.check_no_movement() is not None:
            raise self.printer.command_error(
                "Probe triggered prior to movement")
        return epos

def load_config(config):
    return ProbeTarget(config)
