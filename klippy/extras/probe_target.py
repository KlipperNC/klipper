
from homing import HomingMove


class MCUBase:
    '''
        All MCU's must implement these functions (use ABC for python 3.x)
    '''
    def get_mcu(self):
        raise NotImplemented
    def add_stepper(self):
        raise NotImplemented
    def get_steppers(self):
        raise NotImplemented
    def home_start(self):
        raise NotImplemented
    def home_wait(self):
        raise NotImplemented
    def query_endstop(self):
        raise NotImplemented







# do we create this MCU once when the commands are registered?
# do we create it once we need it with the associated direction of the probing?
#    probably only want to create and register this "virtual" mcu once so there aren't many of them floating around each time the command is executed
#    if this is the case, we'll want to be able to move in xyz and therefore need to add all steppers as active ones




class ProbeMCU(MCUBase):
    '''
        There is a 1-to-1 relationship between stepper motor and endstop. In order to stop a stepper motor based on an
        input, we need to create virtual MCU that ties and existing stepper motor to a new trigger pin.

        pin.Pin contains a reference to its physical MCU (`chip`) and we use this to create a new pin for our endstop

        event `klippy:mcu_identify` to reuse stepper objects from physical MCUs.
    '''
    def __init__(self, printer, pin_params):
        '''
            printer : printer.Printer
            mcu : klippy.MCU
        '''

        self.printer = printer

        # our probe pin is a new endstop for an existing stepper motor
        self._mcu = pin_params['chip'].setup_pin('endstop', pin_params)

        printer.register_event_handler('klippy:mcu_identify', self._handle_mcu_identify)

    def get_mcu(self):
        return self._mcu.get_mcu()

    def add_steppers(self):
        return self._mcu.add_stepper()

    def get_stepper(self):
        return self._mcu.get_steppers()

    def home_start(self):
        return self._mcu.home_start()

    def home_wait(self):
        return self._mcu.home_wait()

    def query_endstop(self):
        return self._mcu.query_endstop()

    # when this new "mcu" is identified, find the stepper and add it as if this mcu owned it
    def _handle_mcu_identify(self):
        kin = self.printer.lookup_object('toolhead').get_kinematics()
        for stepper in kin.get_steppers():
            if stepper.is_active_axis(self.axis):
                # registers a stepper
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
