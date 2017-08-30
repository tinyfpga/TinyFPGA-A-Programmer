import serial
import array
from time import sleep
import re


class Pin(object):
    def __init__(self, index, direction=1):
        self.index = index
        self.direction = direction

    def __get__(self, obj, objtype):
        return obj.get(self.index)

    def __set__(self, obj, val):
        obj.set_direction(self.index, self.direction)
        obj.set(self.index, val)



class Pins(object):
    def __init__(self, ser):
        self.ser = ser
        self.pin_directions = 0
        self.pin_new_directions = 0x3f
        self.pin_output_values = 0
        self.pin_input_values = []
        self.pending_input = 0
        self.byte_queue = []


    def _queue(self, cmd, data):
        byte = ((cmd & 0x3) << 6) | (data & 0x3f)
        self.byte_queue.append(byte)

    def send(self):
        self.ser.write(array.array('B', self.byte_queue).tostring())
        self.byte_queue = []
        if self.pending_input > 0:
            print str([hex(x) for x in array.array('B', self.ser.read(size = self.pending_input)).tolist()])
            self.pending_input = 0


    def set_direction(self, pin, new_direction):
        if new_direction:
            self.pin_new_directions |= (1 << pin)
        else:
            self.pin_new_directions &= ~(1 << pin)


    def set(self, pin, new_value):
        if new_value:
            self.pin_output_values |= (1 << pin)
        else:
            self.pin_output_values &= ~(1 << pin)


    def get(self, pin):
        """
        Return all pending values for the given input pin.
        """
        pass


    def configure(self, directions):
        self._queue(0, directions)

    def update(self, read_back = False):
        if self.pin_directions != self.pin_new_directions:
            self.pin_directions = self.pin_new_directions
            self.configure(self.pin_directions)

        if read_back:
            self._queue(3, self.pin_output_values)
            self.pending_input += 1
        else:
            self._queue(2, self.pin_output_values)




class JtagPins(Pins):
    tms = Pin(5, direction=0)
    tck = Pin(4, direction=0)
    tdi = Pin(3, direction=0)
    tdo = Pin(2, direction=1)


def ntuples(lst, n):
    return zip(*[lst[i:]+lst[:i] for i in range(n)])

class JtagStateMachine(object):
    def __init__(self):
        self.states = {
            "RESET": ("IDLE", "RESET"),
            "IDLE": ("IDLE", "DRSELECT"),

            "DRSELECT": ("DRCAPTURE", "IRSELECT"),
            "DRCAPTURE": ("DRSHIFT", "DREXIT1"),
            "DRSHIFT": ("DRSHIFT", "DREXIT1"),
            "DREXIT1": ("DRPAUSE", "DRUPDATE"),
            "DRPAUSE": ("DRPAUSE", "DREXIT2"),
            "DREXIT2": ("DRSHIFT", "DRUPDATE"),
            "DRUPDATE": ("IDLE", "DRSELECT"),

            "IRSELECT": ("IRCAPTURE", "RESET"),
            "IRCAPTURE": ("IRSHIFT", "IREXIT1"),
            "IRSHIFT": ("IRSHIFT", "IREXIT1"),
            "IREXIT1": ("IRPAUSE", "IRUPDATE"),
            "IRPAUSE": ("IRPAUSE", "IREXIT2"),
            "IREXIT2": ("IRSHIFT", "IRUPDATE"),
            "IRUPDATE": ("IDLE", "DRSELECT")
        }


    def shortest_path(self, source, target):
        """
        This function implements Dijkstra's Algorithm almost exactly as it is
        written on Wikipedia.

        https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
        """
        INFINITY = 1000
        UNDEFINED = None

        q = set()
        dist = {}
        prev = {}

        for v in self.states:
            dist[v] = INFINITY
            prev[v] = UNDEFINED
            q.add(v)

        dist[source] = 0

        while len(q) is not 0:
            u = min(q, key = lambda x: dist[x])
            q.remove(u)

            for v in self.states[u]:
                alt = dist[u] + 1
                if alt < dist[v]:
                    dist[v] = alt
                    prev[v] = u

        s = []
        u = target
        while prev[u] is not None:
            s.insert(0, u)
            u = prev[u]

        s.insert(0, u)

        return s


    def get_tms_sequence(self, source, target):
        def get_tms(pair):
            (src, dst) = pair
            if self.states[src][0] == dst:
                return 0
            elif self.states[src][1] == dst:
                return 1
            else:
                return None

        path = self.shortest_path(source, target)

        return [get_tms(p) for p in ntuples(path, 2)][:-1]
            



class Sentinal(object):
    def __init__(self, val):
        self.val = val


def unwrap(val):
    if isinstance(val, Sentinal):
        return val.val
    else:
        return val

def is_last(val):
    return isinstance(val, Sentinal)


# https://stackoverflow.com/questions/2429098/how-to-treat-the-last-element-in-list-differently-in-python
def with_sentinal(itr):
    itr = iter(itr)  
    prev = itr.next()
    for item in itr:
        yield prev
        prev = item

    yield Sentinal(prev)


class Jtag(object):
    def __init__(self, pins):
        self.pins = pins
        self.sm = JtagStateMachine()
        self.current_state = None

    
    def run_tms(self, tms_sequence):
        for tms in tms_sequence:
            self.pins.tms = tms
            self.pins.tck = 0
            self.pins.update()

            self.pins.tck = 1
            self.pins.update()


        self.pins.send()


    def run(self, tclks, tms):
        self.pins.tms = tms

        for i in range(tclks):
            self.pins.tck = 0
            self.pins.update()

            self.pins.tck = 1
            self.pins.update()


        self.pins.send()


    def goto_state(self, target_state):
        tms_sequence = []

        if self.current_state is None:
            # we don't know what state we're in, so we will force ourselves
            # into the Reset state before we start moving anywhere
            self.current_state = "RESET"
            tms_sequence = [1, 1, 1, 1, 1, 1] + tms_sequence

        tms_sequence = tms_sequence + self.sm.get_tms_sequence(self.current_state, target_state)
        self.run_tms(tms_sequence)
        self.current_state = target_state


    def shift(self, num_bits, tdi, tdo = 0, mask = 0):
        self.pins.tms = 0
        out_data_shift_reg = tdi
        in_mask_shift_reg = mask

        for i in range(num_bits - 1):
            self.pins.tdi = out_data_shift_reg & 1
            self.pins.tck = 0
            self.pins.update()

            self.pins.tck = 1
            self.pins.update(in_mask_shift_reg & 1)

            out_data_shift_reg = out_data_shift_reg >> 1
            in_mask_shift_reg = in_mask_shift_reg >> 1

        self.pins.send()



class JtagSvfParser(object):
    def __init__(self, jtag, svf_file):
        self.jtag = jtag
        self.svf_file = svf_file
        self.hdr = ["hdr", 0]
        self.hir = ["hir", 0]
        self.tdr = ["tdr", 0]
        self.tir = ["tir", 0]
        self.enddr = "DRPAUSE"
        self.endir = "IRPAUSE"

    def run(self):
        def field(cmd, name):
            num_bits = int(cmd[1])
            for k, v in ntuples(cmd, 2):
                if k == name:
                    return int(v, 16)

            return 0

        raw_svf_string = self.svf_file.read()
        no_comment_svf_string = re.sub('!.*?\r?\n', ' ', raw_svf_string)
        no_lines_string = re.sub(r'\s+', ' ', no_comment_svf_string)
        raw_cmd_strings = no_lines_string.lower().split(';')
        cmds = [re.sub(r'\(|\)', '', x).strip().split(' ') for x in raw_cmd_strings]

        for cmd in cmds:
            print str(cmd)
            name = cmd[0]

            if name == "hdr":
                self.hdr = cmd

            if name == "hir":
                self.hir = cmd

            if name == "tdr":
                self.tdr = cmd

            if name == "tir":
                self.tir = cmd

            if name == "enddr":
                self.enddr = cmd[1].upper()

            if name == "endir":
                self.endir = cmd[1].upper()

            if name == "state":
                self.jtag.goto_state(cmd[1].upper())

            if name == "runtest":
                self.jtag.goto_state(cmd[1].upper())

                try:
                    self.jtag.run(int(cmd[2]) - 1, 0)
                except:
                    try:
                        sleep_time = float(cmd[2])
                        print "Sleeping for %f seconds" % sleep_time
                        sleep(sleep_time)
                    except:
                        pass

                try:
                    sleep_time = float(cmd[4])
                    print "Sleeping for %f seconds" % sleep_time
                    sleep(sleep_time)
                except:
                    pass

            if name == "sir":
                self.jtag.goto_state("IRSHIFT")

                #tr_loc = int(self.hir[1]) + int(cmd[1])
                #r_loc = int(self.hir[1])
                #hr_loc = 0

                self.jtag.shift(
                    int(cmd[1]), 
                    #tdi =  (field(self.tir, "tdi")  << tr_loc) | (field(cmd, "tdi")  << r_loc) | (field(self.hir, "tdi")  << hr_loc), 
                    #tdo =  (field(self.tir, "tdo")  << tr_loc) | (field(cmd, "tdo")  << r_loc) | (field(self.hir, "tdo")  << hr_loc), 
                    #mask = (field(self.tir, "mask") << tr_loc) | (field(cmd, "mask") << r_loc) | (field(self.hir, "mask") << hr_loc)
                    tdi  = field(cmd, "tdi"), 
                    tdo  = field(cmd, "tdo"), 
                    mask = field(cmd, "mask")
                )

                self.jtag.goto_state(self.endir)

            if name == "sdr":
                self.jtag.goto_state("DRSHIFT")

                #tr_loc = int(self.hdr[1]) + int(cmd[1])
                #r_loc = int(self.hdr[1])
                #hr_loc = 0

                self.jtag.shift(
                    int(cmd[1]), 
                    #tdi =  (field(self.tdr, "tdi")  << tr_loc) | (field(cmd, "tdi")  << r_loc) | (field(self.hdr, "tdi")  << hr_loc), 
                    #tdo =  (field(self.tdr, "tdo")  << tr_loc) | (field(cmd, "tdo")  << r_loc) | (field(self.hdr, "tdo")  << hr_loc), 
                    #mask = (field(self.tdr, "mask") << tr_loc) | (field(cmd, "mask") << r_loc) | (field(self.hdr, "mask") << hr_loc)
                    tdi  = field(cmd, "tdi"), 
                    tdo  = field(cmd, "tdo"), 
                    mask = field(cmd, "mask")
                )

                self.jtag.goto_state(self.enddr)



#with serial.Serial("COM20", 10000000, timeout=100000000, writeTimeout=100000000) as ser:
#    with open('C:/Users/lvale/Documents/blink_project_2/impl/template_a2_impl.svf', 'r') as svf_file:
#        pins = JtagPins(ser)
#        jtag = Jtag(pins)
#        parser = JtagSvfParser(jtag, svf_file)
#        parser.run()

#    print "Done!"

ser = serial.Serial("COM20", 10000000, timeout=100000000, writeTimeout=100000000)
pins = JtagPins(ser)

def go():
    pins.tck = 1
    pins.tdi = 1
    pins.tms = 1
    pins.update(True)

    pins.tck = 0
    pins.tdi = 0
    pins.tms = 0
    pins.update(True)

    pins.tck = 1
    pins.tdi = 1
    pins.tms = 1
    pins.update(True)

    pins.tck = 0
    pins.tdi = 0
    pins.tms = 0
    pins.update(True)

    pins.tck = 1
    pins.tdi = 1
    pins.tms = 1
    pins.update(True)

    pins.tck = 0
    pins.tdi = 0
    pins.tms = 0
    pins.update(True)

    pins.tck = 1
    pins.tdi = 1
    pins.tms = 1
    pins.update(True)

    pins.tck = 0
    pins.tdi = 0
    pins.tms = 0
    pins.update(True)

    pins.tck = 1
    pins.tdi = 1
    pins.tms = 1
    pins.update(True)

    pins.tck = 0
    pins.tdi = 0
    pins.tms = 0
    pins.update(True)

    pins.tck = 1
    pins.tdi = 1
    pins.tms = 1
    pins.update(True)

    pins.tck = 0
    pins.tdi = 0
    pins.tms = 0
    pins.update(True)

    pins.tck = 1
    pins.tdi = 1
    pins.tms = 1
    pins.update(True)

    pins.tck = 0
    pins.tdi = 0
    pins.tms = 0
    pins.update(True)

    pins.tck = 1
    pins.tdi = 1
    pins.tms = 1
    pins.update(True)

    pins.tck = 0
    pins.tdi = 0
    pins.tms = 0
    pins.update(True)

    pins.send()

