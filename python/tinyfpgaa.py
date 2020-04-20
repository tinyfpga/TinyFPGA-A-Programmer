import serial
import array
import time
import re
import math
import itertools
import traceback

class SyncSerial(object):
    def __init__(self, ser, write_buffer_size = 64, write_flush_timeout = 0.001):
        self.ser = ser
        self.pending_write_data = []
        self.write_buffer_size = write_buffer_size

        ser.flushInput()
        ser.flushOutput()


    def write(self, data):
        if isinstance(data, int):
            self.pending_write_data.append(data)
        else:
            self.pending_write_data.extend(data)

        while len(self.pending_write_data) > self.write_buffer_size:
            write_data = self.pending_write_data[0:63]
            self.pending_write_data = self.pending_write_data[63:]
            self.ser.write(array.array('B', write_data).tostring())
            self.ser.flush()


    def read(self, num_bytes, callback, blocking = False):
        self.flush()
        read_data = [x for x in array.array('B', self.ser.read(size = num_bytes)).tolist()]
        callback(read_data)


    def task(self):
        return 0

    def flush(self):
        if len(self.pending_write_data) > 0:
            self.ser.write(array.array('B', self.pending_write_data).tostring())
            self.pending_write_data = []

        self.ser.flush()



class AsyncSerial(object):
    """
    Async wrapper class for serial objects.  Ensures that write operations are
    buffered and read operations are executed asynchronously with a callback
    function to process each individual read request data.  Read and write
    order is strictly maintained in FIFO order.
    """
    def __init__(self, ser, write_buffer_size = 63, write_flush_timeout = 0.001):
        self.ser = ser
        self.write_buffer_size = write_buffer_size
        self.write_flush_timeout = write_flush_timeout
        self.pending_write_data = []
        self.pending_reads = []
        self.last_write_time = time.time()

        ser.flushInput()
        ser.flushOutput()



    def write(self, data):
        """
        Issue an asynchronous write.
        """
        self.last_write_time = time.time()

        #print "write: " + str(data)

        if isinstance(data, int):
            assert data <= 255
            self.pending_write_data.append(data)
        else:
            for d in data:
                assert d <= 255
            self.pending_write_data.extend(data)


        if len(self.pending_write_data) >= self.write_buffer_size:
            self.task()


    def read(self, num_bytes, callback, blocking = False):
        """
        Issue an asynchronous read.  This read callback is inserted into the
        read queue in the order it was issued.  Once all previous read requests
        have been satisfied and enough bytes are ready for this request the
        callback will be called with the read data.
        """
        if blocking:
            self.flush()
            read_data = [x for x in array.array('B', self.ser.read(size = num_bytes)).tolist()]
            callback(read_data)

        else:
            self.pending_reads.append((num_bytes, callback))

        #self.pending_reads.append((num_bytes, callback))
        #if blocking:
        #    self.flush()
        #    while self.task() > 0:
        #        time.sleep(0.1)
        #    read_data = [x for x in array.array('B', self.ser.read(size = num_bytes)).tolist()]
        #    callback(read_data)

        #else:
        #    self.pending_reads.append((num_bytes, callback))



    def task(self):
        """
        Call periodically in the thread you want read callbacks to execute in.
        """
        while len(self.pending_reads) > 0:
            num_bytes = self.pending_reads[0][0]
            callback = self.pending_reads[0][1]
            ser_in_waiting = self.ser.inWaiting()
            #print "ser.inWaiting(): " + str(ser_in_waiting)
            if ser_in_waiting >= num_bytes:
                #print "reading pending read data: " + str(num_bytes)
                read_data = [x for x in array.array('B', self.ser.read(size = num_bytes)).tolist()]
                #print "    read callback: %d, %s = %s" % (num_bytes, str(callback), str(read_data))
                callback(read_data)
                self.pending_reads.pop(0)
            else:
                break

        while len(self.pending_write_data) >= self.write_buffer_size:
            #print "writing pending write data: " + str(len(self.pending_write_data))
            write_data = self.pending_write_data[0:63]
            self.pending_write_data = self.pending_write_data[63:]
            self.ser.write(array.array('B', write_data).tostring())
            self.ser.flush()

        flush_timeout_expired = (time.time() - self.last_write_time) >= self.write_flush_timeout
        more_data_to_write = len(self.pending_write_data) > 0

        if flush_timeout_expired and more_data_to_write:
            self.flush()

        return len(self.pending_reads) + len(self.pending_write_data)

    def flush(self):
        if len(self.pending_write_data) > 0:
            self.ser.write(array.array('B', self.pending_write_data).tostring())
            self.ser.flush()
            self.pending_write_data = []

        #while len(self.pending_write_data) >= self.write_buffer_size:
        #    #print "writing pending write data: " + str(len(self.pending_write_data))
        #    write_data = self.pending_write_data[0:63]
        #    self.pending_write_data = self.pending_write_data[63:]
        #    self.ser.write(array.array('B', write_data).tostring())
        #    self.ser.flush()
        #
        #if len(self.pending_write_data) > 0:
        #    self.ser.write(self.pending_write_data)
        #    self.pending_write_data = []
        #    self.ser.flush()



class Pin(object):
    """
    Property that represents an individual GPIO pin on the TinyFPGA Programmer
    board. This allows for the GPIO pins to be referenced by a name rather than
    an index number.  This is to be used with the TinyFpgaProgrammer class.
    """
    def __init__(self, index, direction=1):
        self.index = index
        self.direction = direction

    def __get__(self, obj, objtype):
        return None

    def __set__(self, obj, val):
        obj.set_direction(self.index, self.direction)
        obj.set(self.index, val)


        self.sie_does_input = {}
        self.sie_does_output = {}



class TinyFpgaProgrammer(object):
    """
    Represents the TinyFPGA Programmer hardware.  All of the commands the board
    can process can be accessed through the functions on this class.
    """
    def __init__(self, ser):
        self.ser = ser
        self.pin_directions = 0
        self.pin_new_directions = 0x3f
        self.pin_output_values = 0
        self.pending_input = 0

        self.in_loop_body = False
        self.loop_iter_count = 0
        self.loop_byte_count = 0
        self.loop_body = []

        self.sie_gets_input = {}
        self.sie_sends_output = {}
        self.sie_has_mask = {}


    def _cmd(self, cmd, data):
        byte = ((cmd & 0x3) << 6) | (data & 0x3f)

        if self.in_loop_body:
            self.loop_byte_count += 1
            self.loop_body.append(byte)
        else:
            self.ser.write(byte)


    def send(self, num_read_bytes = None, read_callback = None, blocking = False):
        """
        Asynchronously sends any pending commands.  If you sent a series
        of GPIO commands expecting read data you must also send a read_callback
        that will process the read data when it arrives.
        """
        self.ser.task()

        num_bytes_to_read = self.pending_input
        if num_read_bytes is not None:
            assert self.pending_input == 0
            num_bytes_to_read = num_read_bytes

        if num_bytes_to_read > 0:
            self.ser.flush()
            self.ser.read(num_bytes = num_bytes_to_read, callback = read_callback, blocking = blocking)
            self.pending_input = 0


    def set_direction(self, pin, new_direction):
        """
        Set the direction of a pin by id.
        """
        if new_direction:
            self.pin_new_directions |= (1 << pin)
        else:
            self.pin_new_directions &= ~(1 << pin)


    def set(self, pin, new_value):
        """
        Set the value of a pin by id.
        """
        if new_value:
            self.pin_output_values |= (1 << pin)
        else:
            self.pin_output_values &= ~(1 << pin)


    def update(self, read_back = False):
        """
        Capture current GPIO values and send them to the TinyFPGA Programmer.
        """
        if self.in_loop_body:
            assert read_back == False

        #if self.pin_directions != self.pin_new_directions:
        #    self.pin_directions = self.pin_new_directions
        #    self.configure_io(self.pin_directions)

        if read_back:
            self._cmd(2, self.pin_output_values)
            self.pending_input += 1
        else:
            self._cmd(1, self.pin_output_values)

    def clear_status(self):
        self.ser.write(0x20)

    def get_status(self, status_callback, blocking = True):
        self.ser.write(0x21)
        self.ser.read(1, status_callback, blocking = blocking)




    def configure_io(self, directions):
        """
        Configure input/output direction of GPIO pins.
        """
        CONFIG_IO_CMD = [0x00, directions]

        if self.in_loop_body:
            self.loop_byte_count += len(CONFIG_IO_CMD)
            self.loop_body += CONFIG_IO_CMD
        else:
            self.ser.write(CONFIG_IO_CMD)

    def _int_to_byte_list(self, num_bytes, data):
        byte_list = []

        for i in range(0, num_bytes):
            byte_list.append(data & 0xff)
            data = data >> 8

        return byte_list


    def _encode(self, number):
        num_bytes = int(number / 8)
        num_bits = number % 8

        if num_bits == 0 and num_bytes > 0:
            num_bits = 8
            num_bytes -= 1

        return [num_bits, num_bytes]


    def shift(self, sie_id, num_bits, data = 0, mask = 0, read_callback = None, blocking = False):
        """
        Issue an accelerated shift operation.  For shifting serial data in
        and out of the TinyFPGA Programmer, this is the prefered method.  It
        is much faster than GPIO bit-bang.
        """
        assert sie_id >= 0 and sie_id <= 7

        SHIFT_CMD = 0x18 + sie_id

        do_input = self.sie_gets_input[sie_id]
        do_output = self.sie_sends_output[sie_id]
        do_mask = self.sie_has_mask[sie_id]

        num_bytes = int(math.ceil(num_bits / 8.0))

        shift_cmd_bytes = [SHIFT_CMD] + self._encode(num_bits)

        if do_output and do_mask:
            iters = [
                iter(self._int_to_byte_list(num_bytes, data)),
                iter(self._int_to_byte_list(num_bytes, mask))]

            payload_bytes = list()
            for it in itertools.cycle(iters):
                try:
                    payload_bytes.append(next(it))
                except StopIteration:
                    break

            shift_cmd_bytes += payload_bytes

        elif do_output:
            shift_cmd_bytes += self._int_to_byte_list(num_bytes, data)

        if self.in_loop_body:
            self.loop_byte_count += len(shift_cmd_bytes)
            self.loop_body += shift_cmd_bytes

        else:
            self.ser.write(shift_cmd_bytes)

            if do_input:
                self.send(num_read_bytes = num_bytes, read_callback = read_callback, blocking = blocking)

            elif do_output and do_mask:
                if read_callback is None:
                    self.send()
                else:
                    self.send(num_read_bytes = 1, read_callback = read_callback, blocking = blocking)


    def configure_sie(self,
        sie_id,
        sends_output,
        input_on_phase0,
        input_on_phase1,
        has_input_mask,
        input_mask,
        do0p0,
        do0p1,
        do1p0,
        do1p1,
        last_phase_overlay
    ):
        """
        Configure the serial interface engine.
        """
        assert self.in_loop_body == False
        assert sie_id >= 0 and sie_id <= 7

        self.sie_gets_input[sie_id] = (input_on_phase0 or input_on_phase1) and not has_input_mask
        self.sie_sends_output[sie_id] = sends_output or has_input_mask
        self.sie_has_mask[sie_id] = has_input_mask

        CONFIG_SIE_CMD = 8 + sie_id

        config_byte = 0
        if sends_output:    config_byte |= 1
        if input_on_phase0: config_byte |= 2
        if input_on_phase1: config_byte |= 4
        if has_input_mask:  config_byte |= 8

        self.ser.write([
            CONFIG_SIE_CMD,
            config_byte,
            input_mask,
            do0p0,
            do0p1,
            do1p0,
            do1p1,
            last_phase_overlay
        ])


    def loop(self, iter_count):
        """
        Begin a loop definition.  Loops are very efficient for polling a status
        bit from the hardware.  The loop can be executed completely within the
        TinyFPGA Programmer firmware.  Because of this, any polling data can be
        checked within the firmware and does not need to be sent back to the
        host computer over USB to be processed.  This saves 1-2 milliseconds
        per loop iteration.

        Loops cannot be nested.
        """
        assert self.in_loop_body == False

        self.in_loop_body = True
        self.loop_iter_count = iter_count
        self.loop_byte_count = 0
        self.loop_body = []


    def end_loop(self, status_callback):
        """
        End a loop definition.  The status_callback will be called with a
        single byte list indicating 0 if no loop iterations remain and
        1 if there were more loop iterations remaining.
        """

        # FW doesn't have another buffer for loops, so we need to make sure
        # the entire loop encoding fits in one packet.
        self.ser.flush()

        LOOP_CMD = 0x10
        END_LOOP_CMD = 0x11

        self.ser.write(
            [LOOP_CMD] +
            [self.loop_iter_count & 0xff, self.loop_iter_count >> 8] +
            self.loop_body +
            [END_LOOP_CMD]
        )

        self.in_loop_body = False

        #self.send(num_read_bytes = 1, read_callback = status_callback)
        self.send()



class JtagTinyFpgaProgrammer(TinyFpgaProgrammer):
    tms = Pin(5, direction=0)
    tck = Pin(4, direction=0)
    tdi = Pin(3, direction=0)
    tdo = Pin(2, direction=1)


    def __init__(self, ser):
        TinyFpgaProgrammer.__init__(self, ser)

        ### manually set TMS, TCK, and TDI to output and TDO to input
        self.configure_io(0b000111)

        ### setup serial interface engine parameters for JTAG
        # run_tck
        self.configure_sie(
            sie_id = 0,
            sends_output = 0,
            input_on_phase0 = 0,
            input_on_phase1 = 0,
            has_input_mask = 0,
            input_mask = 0,
            do0p0 = 0x00,
            do0p1 = 0x10,
            do1p0 = 0x00,
            do1p1 = 0x10,
            last_phase_overlay = 0x00)

        # shift_tms
        self.configure_sie(
            sie_id = 1,
            sends_output = 1,
            input_on_phase0 = 0,
            input_on_phase1 = 0,
            has_input_mask = 0,
            input_mask = 0,
            do0p0 = 0x00,
            do0p1 = 0x10,
            do1p0 = 0x20,
            do1p1 = 0x30,
            last_phase_overlay = 0x00)

        # shift_tdi
        self.configure_sie(
            sie_id = 2,
            sends_output = 1,
            input_on_phase0 = 0,
            input_on_phase1 = 0,
            has_input_mask = 0,
            input_mask = 0,
            do0p0 = 0x00,
            do0p1 = 0x10,
            do1p0 = 0x08,
            do1p1 = 0x18,
            last_phase_overlay = 0x20)

        # shift_tdo
        self.configure_sie(
            sie_id = 3,
            sends_output = 0,
            input_on_phase0 = 0,
            input_on_phase1 = 1,
            has_input_mask = 0,
            input_mask = 0x04,
            do0p0 = 0x00,
            do0p1 = 0x10,
            do1p0 = 0x00,
            do1p1 = 0x10,
            last_phase_overlay = 0x20)

        # shift_tdo_poll
        self.configure_sie(
            sie_id = 4,
            sends_output = 0,
            input_on_phase0 = 0,
            input_on_phase1 = 1,
            has_input_mask = 1,
            input_mask = 0x04,
            do0p0 = 0x00,
            do0p1 = 0x10,
            do1p0 = 0x00,
            do1p1 = 0x10,
            last_phase_overlay = 0x20)


    def run_tck(self, num_clks):
        self.shift(sie_id = 0, num_bits = num_clks)


    def shift_tms(self, num_bits, data):
        self.shift(sie_id = 1, num_bits = num_bits, data = data)


    def shift_tdi(self, num_bits, data):
        self.shift(sie_id = 2, num_bits = num_bits, data = data)


    def shift_tdo(self, num_bits, read_callback, blocking = False):
        self.shift(sie_id = 3, num_bits = num_bits, read_callback = read_callback, blocking = blocking)


    def shift_tdo_poll(self, num_bits, data, mask, status_callback):
        self.shift(sie_id = 4, num_bits = num_bits, data = data, mask = mask, read_callback = None)
        # FIXME: need to enable mode to send data without mask


def ntuples(lst, n):
    return list(zip(*[lst[i:]+lst[:i] for i in range(n)]))



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

        self.memo = {}

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

        while len(q) != 0:
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
        memo_key = (source, target)
        if memo_key in self.memo:
            return self.memo[memo_key]

        def get_tms(pair):
            (src, dst) = pair
            if self.states[src][0] == dst:
                return 0
            elif self.states[src][1] == dst:
                return 1
            else:
                return None

        path = self.shortest_path(source, target)
        tms_sequence = [get_tms(p) for p in ntuples(path, 2)][:-1]
        self.memo[memo_key] = tms_sequence

        return tms_sequence



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
    prev = next(itr)
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
        #data = 0
        #for i, v in enumerate(tms_sequence):
        #    data |= v << i
        #self.pins.shift_tms(len(tms_sequence), data)

        for tms in tms_sequence:
            self.pins.tms = tms
            self.pins.tck = 0
            self.pins.update()

            self.pins.tck = 1
            self.pins.update()


        #self.pins.send()


    def run(self, tclks, tms):
        self.pins.tms = tms
        self.pins.update()
        while tclks > 0:
            tclks_now = min(tclks, 1000)
            self.pins.run_tck(tclks_now)
            tclks -= tclks_now
            self.pins.send()

        # for i in range(tclks):
        #     self.pins.tck = 0
        #     self.pins.update()
        #
        #     self.pins.tck = 1
        #     self.pins.update()
        # self.pins.send()


    def goto_state(self, target_state):
        tms_sequence = []

        if self.current_state is None:
            # we don't know what state we're in, so we will force ourselves
            # into the Reset state before we start moving anywhere
            self.current_state = "RESET"
            tms_sequence = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1] + tms_sequence

        tms_sequence = tms_sequence + self.sm.get_tms_sequence(self.current_state, target_state)
        self.run_tms(tms_sequence)
        self.current_state = target_state


    #tms = Pin(5, direction=0)
    #tck = Pin(4, direction=0)
    #tdi = Pin(3, direction=0)
    #tdo = Pin(2, direction=1)

    def shift(self, num_bits, tdi, tdo = 0, mask = 0, status_callback = None):
        self.pins.tms = 0
        self.pins.update()

        out_data_shift_reg = tdi
        read_back = mask > 0

        if num_bits > 0:
            if read_back:
                def check_read_data(read_data):
                    #print "  check_read_data(" + str(read_data) + ")"

                    read_bits = 0

                    for i, v in enumerate(read_data):
                        read_bits |= v << (i * 8)

                    match = (tdo & mask) == (read_bits & mask)

                    if status_callback is not None:
                        if not match:
                            print("")
                            print("        read data: 0x%032x" % read_bits)
                            print("    expected data: 0x%032x" % tdo)
                            print("        mask data: 0x%032x" % mask)
                        status_callback(match)

                self.pins.shift_tdo(num_bits, check_read_data)
                self.current_state = self.sm.states[self.current_state][1]
                return
                #pass

            else:
                self.pins.shift_tdi(num_bits, tdi)
                self.current_state = self.sm.states[self.current_state][1]
                return


        for i in range(num_bits - 1):
            self.pins.tdi = out_data_shift_reg & 1
            self.pins.tck = 0
            self.pins.update()

            self.pins.tck = 1
            self.pins.update(read_back)

            out_data_shift_reg = out_data_shift_reg >> 1



        # last shift
        self.pins.tdi = out_data_shift_reg & 1
        self.pins.tck = 0
        self.pins.tms = 1
        self.pins.update()

        self.pins.tck = 1
        self.pins.update(read_back)

        self.current_state = self.sm.states[self.current_state][1]

        if read_back:
            def check_read_data(read_data):
                #print "  check_read_data(" + str(read_data) + ")"
                read_bits = 0
                index = 0
                for b in read_data:
                    bit = 0
                    if (b & 4) > 0:
                        bit = 1

                    read_bits = read_bits | (bit << index)
                    index += 1

                match = (tdo & mask) == (read_bits & mask)

                if status_callback is not None:
                    status_callback(match)

            self.pins.send(read_callback = check_read_data)




def do_for(num_seconds, function):
    timeout = time.time() + num_seconds
    while time.time() < timeout:
        function()


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
        self.loop_count = [0]

    def run(self):
        def field(cmd, name):
            num_bits = int(cmd[1])
            for k, v in ntuples(cmd, 2):
                if k == name:
                    return int(v, 16)

            if name == "mask" and "tdo" in cmd:
                return (2 ** num_bits) - 1
            else:
                return 0

        def runtest_field(cmd, name):
            for v, k in ntuples(cmd, 2):
                if k == name:
                    return v

            return None

        raw_svf_string = self.svf_file.read()
        no_comment_svf_string = re.sub('!.*?\r?\n', ' ', raw_svf_string)
        no_lines_string = re.sub(r'\s+', ' ', no_comment_svf_string)
        raw_cmd_strings = no_lines_string.lower().split(';')
        cmds = [re.sub(r'\(|\)', '', x).strip().split(' ') for x in raw_cmd_strings]

        loop_index = None
        self.loop_count = [0]
        cmd_index = 0

        while cmd_index < len(cmds):
            cmd = cmds[cmd_index]
            cmd_index = cmd_index + 1

            #print str(cmd)

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

            if name == "loop":
                self.loop_count = [int(cmd[1])] * 1000
                #print "loop (loop_count: %d)" % self.loop_count[0]
                loop_index = cmd_index

            if name == "endloop":
                #print "endloop (loop_count: %d)" % self.loop_count[0]
                if self.loop_count[0] is None:
                    loop_index = None
                else:
                    self.loop_count[0] = self.loop_count[0] - 1

                    if self.loop_count[0] > 0:
                        cmd_index = loop_index
                    else:
                        self.loop_count[0] = None
                        loop_index = None


            if name == "runtest":
                self.jtag.goto_state(cmd[1].upper())

                sleep_time = runtest_field(cmd, "sec")
                tck_count = runtest_field(cmd, "tck")

                if tck_count is None:
                    tck_count = 0
                else:
                    tck_count = int(tck_count)

                if sleep_time is not None:
                    tck_count = max(float(sleep_time) / 0.00001, tck_count)

                self.jtag.run(int(tck_count), 0)

            if name == "sir":
                self.jtag.goto_state("IRSHIFT")

                #tr_loc = int(self.hir[1]) + int(cmd[1])
                #r_loc = int(self.hir[1])
                #hr_loc = 0
                loop_count = self.loop_count
                def status_callback(match):
                    if loop_count[0] is not None:
                        if not match and loop_count[0] <= 1:
                            print("MISMATCH!")
                            print("cmd %d: %s" % (cmd_index, str(cmd)))
                            print("")
                            exit()

                        if match:
                            #print "SIR MATCH! " + str(loop_count)
                            loop_count[0] = 0

                self.jtag.shift(
                    int(cmd[1]),
                    #tdi =  (field(self.tir, "tdi")  << tr_loc) | (field(cmd, "tdi")  << r_loc) | (field(self.hir, "tdi")  << hr_loc),
                    #tdo =  (field(self.tir, "tdo")  << tr_loc) | (field(cmd, "tdo")  << r_loc) | (field(self.hir, "tdo")  << hr_loc),
                    #mask = (field(self.tir, "mask") << tr_loc) | (field(cmd, "mask") << r_loc) | (field(self.hir, "mask") << hr_loc)
                    tdi  = field(cmd, "tdi"),
                    tdo  = field(cmd, "tdo"),
                    mask = field(cmd, "mask"),
                    status_callback = status_callback
                )

                self.jtag.goto_state(self.endir)

            if name == "sdr":
                self.jtag.goto_state("DRSHIFT")

                shift_count = int(cmd[1])

                tr_loc = int(self.hdr[1]) + shift_count
                r_loc = int(self.hdr[1])
                hr_loc = 0

                loop_count = self.loop_count
                def status_callback(match):
                    if loop_count[0] is not None:
                        if not match and loop_count[0] <= 1:
                            print("MISMATCH!")
                            print("cmd %d: %s" % (cmd_index, str(cmd)))
                            print("")
                            exit()

                        if match:
                            #print "SDR MATCH! " + str(loop_count)
                            loop_count[0] = None

                self.jtag.shift(
                    int(cmd[1]),
                    #tdi =  (field(self.tdr, "tdi")  << tr_loc) | (field(cmd, "tdi")  << r_loc) | (field(self.hdr, "tdi")  << hr_loc),
                    #tdo =  (field(self.tdr, "tdo")  << tr_loc) | (field(cmd, "tdo")  << r_loc) | (field(self.hdr, "tdo")  << hr_loc),
                    #mask = (field(self.tdr, "mask") << tr_loc) | (field(cmd, "mask") << r_loc) | (field(self.hdr, "mask") << hr_loc)
                    tdi  = field(cmd, "tdi"),
                    tdo  = field(cmd, "tdo"),
                    mask = field(cmd, "mask"),
                    status_callback = status_callback
                )

                self.jtag.goto_state(self.enddr)

            self.jtag.pins.ser.task()


        self.jtag.pins.send()



class JedecFile(object):
    def __init__(self, jed_file):
        self.cfg_data = None
        self.ebr_data = None
        self.ufm_data = None
        self.feature_row = None
        self.feature_bits = None
        self.last_note = ""
        self._parse(jed_file)

    def numRows(self):
        def toInt(list_or_none):
            if list_or_none is None:
                return 0
            else:
                return len(list_or_none)

        return toInt(self.cfg_data) + toInt(self.ebr_data) + toInt(self.ufm_data)

    def _parse(self, jed):
        def line_to_int(line):
            try:
                return int(line[::-1], 2)
            except:
                traceback.print_exc()
                return None

        def line_is_end_of_field(line):
            return "*" in line

        def line_is_end_of_file(line):
            return r"\x03" in line

        def process_field(field):
            if field[0][0:4] == "NOTE":
                self.last_note = field[0][5:-1]

            elif field[0][0] == "L":
                data = []

                for fuse_string in field[1:-1]:
                    fuse_data = line_to_int(fuse_string)

                    if fuse_data is not None:
                        data.append(fuse_data)

                if "EBR_INIT DATA" in self.last_note:
                    self.ebr_data = data

                elif "END CONFIG DATA" in self.last_note:
                    pass # ignore this data

                elif "TAG DATA" in self.last_note:
                    self.ufm_data = data

                else:
                    self.cfg_data = data

            elif field[0][0] == "E":
                self.feature_row = line_to_int(field[0][1:])
                self.feature_bits = line_to_int(field[1][:-1])



        lines = iter(jed)

        try:
            line = next(lines).strip()

            while True:
                current_field = [line]

                while not line_is_end_of_field(line):
                    line = next(lines).strip()
                    current_field.append(line)

                process_field(current_field)

                line = next(lines).strip()

        except StopIteration:
            pass




class JtagCustomProgrammer(object):
    def __init__(self, jtag):
        self.jtag = jtag
        self.enddr = "DRPAUSE"
        self.endir = "IRPAUSE"
        self.config_data = None

    def write_ir(self, num_bits, write_data):
         self.jtag.goto_state("IRSHIFT")
         self.jtag.pins.shift_tdi(num_bits, write_data)
         self.jtag.current_state = self.jtag.sm.states[self.jtag.current_state][1]
         self.jtag.goto_state("IRPAUSE")

    def read_dr(self, num_bits, read_callback, blocking = False):
         self.jtag.goto_state("DRSHIFT")
         self.jtag.pins.shift_tdo(num_bits, read_callback, blocking = blocking)
         self.jtag.current_state = self.jtag.sm.states[self.jtag.current_state][1]
         self.jtag.goto_state("DRPAUSE")

    def write_dr(self, num_bits, write_data):
         self.jtag.goto_state("DRSHIFT")
         self.jtag.pins.shift_tdi(num_bits, write_data)
         self.jtag.current_state = self.jtag.sm.states[self.jtag.current_state][1]
         self.jtag.goto_state("DRPAUSE")

    def check_dr(self, num_bits, check_data, check_mask, status_callback = None):
         self.jtag.goto_state("DRSHIFT")
         self.jtag.pins.shift_tdo_poll(num_bits, check_data, check_mask, status_callback)
         self.jtag.current_state = self.jtag.sm.states[self.jtag.current_state][1]
         self.jtag.goto_state("DRPAUSE")

    def runtest(self, clks, state = "IDLE"):
        self.jtag.goto_state(state)

        while clks > 0:
            clks_now = min(clks, 1000)
            self.jtag.pins.run_tck(clks_now)
            clks -= clks_now

    def loop(self, loop_count):
        self.jtag.pins.loop(loop_count)

    def endloop(self):
        self.jtag.pins.end_loop(None)



    def program(self, jed_file, progress = None):
        num_rows = jed_file.numRows()
        prog_update_freq = 20
        prog_update_cnt = 0

        def default_progress(v):
            pass

        if progress is None:
            progress = default_progress

        def status(description, amount):
            def status_callback(status):
                if len(status) == 0:
                    progress(description)
                    progress(amount)

                elif status[0] == 0:
                    progress(description)
                    progress(amount)

                else:
                    progress(description + " - Failed!")

            return status_callback

        # drain any lingering read data before continuing
        if self.jtag.pins.ser.ser.inWaiting() > 0:
            print(str([x for x in array.array('B', self.jtag.pins.ser.ser.read(size = self.jtag.pins.ser.ser.inWaiting())).tolist()]))

        self.jtag.pins.clear_status()

        ### read idcode
        # This is constantly being checked in the GUI
        #self.write_ir(8, 0xE0)
        #self.check_dr(32, 0x012BA043, 0xFFFFFFFF)

        ### program bscan register
        self.write_ir(8, 0x1C)
        self.write_dr(208, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

        ### check key protection fuses
        self.write_ir(8, 0x3C)
        self.runtest(1000)
        self.check_dr(32, 0x00000000, 0x00010000)

        ### enable the flash
        # ISC ENABLE
        self.write_ir(8, 0xC6)
        self.write_dr(8, 0x00)
        self.runtest(1000)
        # ISC ERASE
        self.write_ir(8, 0x0E)
        self.write_dr(8, 0x01)
        self.runtest(1000)
        # BYPASS
        self.write_ir(8, 0xFF)
        # ISC ENABLE
        self.write_ir(8, 0xC6)
        self.write_dr(8, 0x08)
        self.runtest(1000)

        ### check the OTP fuses
        # LSC_READ_STATUS
        self.write_ir(8, 0x3C)
        self.runtest(1000)
        self.check_dr(32, 0x00000000, 0x00024040)

        progress("Erasing configuration flash")
        ### erase the flash
        # ISC ERASE
        self.write_ir(8, 0x0E)
        self.write_dr(8, 0x0E)
        self.runtest(1000)
        # LSC_CHECK_BUSY
        self.write_ir(8, 0xF0)
        self.loop(10000)
        self.runtest(1000)
        self.check_dr(1, 0, 1)
        self.endloop()
        self.jtag.pins.get_status(status("Writing bitstream", num_rows), blocking = True)

        ### read the status bit
        # LSC_READ_STATUS
        self.write_ir(8, 0x3C)
        self.runtest(1000)
        self.check_dr(32, 0x00000000, 0x00003000)

        ### program config flash
        # LSC_INIT_ADDRESS
        self.write_ir(8, 0x46)
        self.write_dr(8, 0x04)
        self.runtest(1000)

        row_count = num_rows
        combined_cfg_data = jed_file.cfg_data

        if jed_file.ebr_data is not None:
            combined_cfg_data += jed_file.ebr_data

        for line in combined_cfg_data:
            # LSC_PROG_INCR_NV
            self.write_ir(8, 0x70)
            self.write_dr(128, line)
            self.runtest(2)
            # LSC_CHECK_BUSY
            self.write_ir(8, 0xF0)
            self.loop(10000)
            self.runtest(100)
            self.check_dr(1, 0, 1)
            self.endloop()

            prog_update_cnt += 1

            if prog_update_cnt % prog_update_freq == 0:
                self.jtag.pins.get_status(status("Writing bitstream", prog_update_freq), blocking = True)

        if jed_file.ufm_data is not None:
            ### program user flash
            # LSC_INIT_ADDRESS
            self.write_ir(8, 0x47)
            self.runtest(1000)

            for line in jed_file.ufm_data:
                # LSC_PROG_INCR_NV
                self.write_ir(8, 0x70)
                self.write_dr(128, line)
                self.runtest(2)
                # LSC_CHECK_BUSY
                self.write_ir(8, 0xF0)
                self.loop(10000)
                self.runtest(100)
                self.check_dr(1, 0, 1)
                self.endloop()

                prog_update_cnt += 1

                if prog_update_cnt % prog_update_freq == 0:
                    self.jtag.pins.get_status(status("Writing bitstream", prog_update_freq), blocking = True)

        ### verify config flash
        # LSC_INIT_ADDRESS
        self.write_ir(8, 0x46)
        self.write_dr(8, 0x04)
        self.runtest(1000)

        # LSC_READ_INCR_NV
        self.write_ir(8, 0x73)
        self.feature_row = None
        self.feature_bits = None

        for line in combined_cfg_data:
            self.runtest(2)
            self.check_dr(128, line, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

            prog_update_cnt += 1

            if prog_update_cnt % prog_update_freq == 0:
                self.jtag.pins.get_status(status("Verifying bitstream", prog_update_freq), blocking = True)

        if jed_file.ufm_data is not None:
            ### verify user flash
            # LSC_INIT_ADDRESS
            self.write_ir(8, 0x47)
            self.runtest(1000)

            # LSC_READ_INCR_NV
            self.write_ir(8, 0x73)

            for line in jed_file.ufm_data:
                self.runtest(2)
                self.check_dr(128, line, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

                prog_update_cnt += 1

                if prog_update_cnt % prog_update_freq == 0:
                    self.jtag.pins.get_status(status("Verifying bitstream", prog_update_freq), blocking = True)


        self.jtag.pins.get_status(status("Writing and verifying feature rows", 0), blocking = True)
        ### program feature rows
        # LSC_INIT_ADDRESS
        self.write_ir(8, 0x46)
        self.write_dr(8, 0x02)
        self.runtest(2)
        # LSC_PROG_FEATURE
        self.write_ir(8, 0xE4)
        self.write_dr(64, jed_file.feature_row)
        self.runtest(2)
        # LSC_CHECK_BUSY
        self.write_ir(8, 0xF0)
        self.loop(10000)
        self.runtest(100)
        self.check_dr(1, 0, 1)
        self.endloop()
        # LSC_READ_FEATURE
        self.write_ir(8, 0xE7)
        self.runtest(2)
        self.check_dr(64, jed_file.feature_row, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        # LSC_PROG_FEABITS
        self.write_ir(8, 0xF8)
        self.write_dr(16, jed_file.feature_bits)
        self.runtest(2)
        # LSC_CHECK_BUSY
        self.write_ir(8, 0xF0)
        self.loop(10000)
        self.runtest(100)
        self.check_dr(1, 0, 1)
        self.endloop()
        # LSC_READ_FEABITS
        self.write_ir(8, 0xFB)
        self.runtest(2)
        self.check_dr(16, jed_file.feature_bits, 0xFFFF)

        ### read the status bit
        self.write_ir(8, 0x3C)
        self.runtest(2)
        self.check_dr(32, 0x00000000, 0x00003000)

        ### program done bit
        # ISC PROGRAM DONE
        self.write_ir(8, 0x5E)
        self.runtest(2)
        self.write_dr(8, 0xF0)
        # LSC_CHECK_BUSY
        self.write_ir(8, 0xF0)
        self.loop(10000)
        self.runtest(100)
        self.check_dr(1, 0, 1)
        self.endloop()
        # BYPASS
        self.write_ir(8, 0xFF)

        ### exit programming mode
        # ISC DISABLE
        self.write_ir(8, 0x26)
        self.runtest(1000)
        # ISC BYPASS
        self.write_ir(8, 0xFF)
        self.runtest(1000)

        ### verify sram done bit
        self.runtest(10000)
        # LSC_READ_STATUS
        self.write_ir(8, 0x3C)
        self.check_dr(32, 0x00000100, 0x00002100)

        self.jtag.goto_state("RESET")

        self.jtag.pins.get_status(status("Done", 0), blocking = True)











#import sys

#serial_port_name = sys.argv[1]
#svf_filename = sys.argv[2]

#with serial.Serial(serial_port_name, 12000000, timeout=10, writeTimeout=10) as ser:
#    with open(svf_filename, 'r') as svf_file:
#        async_serial = AsyncSerial(ser)
#        pins = JtagTinyFpgaProgrammer(async_serial)
#        jtag = Jtag(pins)
#        #parser = JtagSvfParser(jtag, svf_file)
#        programmer = JtagCustomProgrammer(jtag)
#        programmer.program(JedecFile(svf_file))



        #pins.tck = 0
        #pins.tdi = 0
        #pins.tms = 0
        #pins.update()
        #pins.shift(None)
        #pins.send()

#    print "Done!"
