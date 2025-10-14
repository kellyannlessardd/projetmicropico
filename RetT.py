
from machine import ADC, Pin, UART, PWM
import time

#Transmitter
# --- Configuration ---
PWM_PIN = 15        # GP15 for PWM output
UART_ID = 0         # UART0 (TX=GP0, RX=GP1)
UART_BAUD = 115200
FREQ = 1000         # PWM frequency in Hz

# --- Setup ---
pwm = PWM(Pin(PWM_PIN))
pwm.freq(FREQ)

uart = UART(UART_ID, baudrate=UART_BAUD)

# Keep current duty as percentage (0.0 - 100.0)
duty_percent = 50.0

# helper to convert percent -> 16-bit duty (MicroPython uses 16-bit for duty)
def set_duty(percent: float):
    global duty_percent
    if percent < 0.0:
        percent = 0.0
    if percent > 100.0:
        percent = 100.0
    duty_percent = percent
    duty_u16 = int((percent / 100.0) * 65535)
    pwm.duty_u16(duty_u16)

# Send the desired duty to receiver via UART
def send_setpoint():
    msg = "SET:{:.2f}\n".format(duty_percent)
    uart.write(msg.encode())

# Read any incoming UART lines (non-blocking) and print them
def read_uart_lines():
    if uart.any():
        try:
            line = uart.readline()
            if line:
                try:
                    # uart.readline() may return bytes or str depending on environment
                    if isinstance(line, bytes):
                        s = line.decode().strip()
                    else:
                        s = str(line).strip()
                    print("UART RX:", s)
                except Exception:
                    print("UART RX (raw):", line)
        except Exception:
            pass

# Example demo routine: ramp duty 0 -> 100 -> 0
def demo_ramp(step=5.0, hold_time=0.05):
    # ramp up
    p = 0.0
    while p <= 100.0:
        set_duty(p)
        send_setpoint()
        read_uart_lines()
        time.sleep(hold_time)
        p += step
    # ramp down
    p = 100.0
    while p >= 0.0:
        set_duty(p)
        send_setpoint()
        read_uart_lines()
        time.sleep(hold_time)
        p -= step

# Main loop
if __name__ == '__main__':
    print("PWM transmitter starting: pin GP{} freq {}Hz".format(PWM_PIN, FREQ))
    set_duty(duty_percent)

    try:
        while True:
            # Send setpoint every 1s and print any measurements
            send_setpoint()
            # Poll UART for a short period
            t0 = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), t0) < 1000:
                read_uart_lines()
                time.sleep(0.05)

            # Optional: you can call demo_ramp() once to exercise
            # demo_ramp()

    except KeyboardInterrupt:
        print("Stopped by user")
        pwm.deinit()


#Receiver

# --- Configuration ---
ADC_PIN = 26        # GP26 (ADC0)
UART_ID = 0
UART_BAUD = 115200
SAMPLES = 200       # number of ADC samples to average
VREF = 3.3          # reference voltage (3.3V typical for Pico)

adc = ADC(Pin(ADC_PIN))
uart = UART(UART_ID, baudrate=UART_BAUD)

expected_setpoint = None

# Read averaged ADC voltage (returns voltage in volts)
def read_avg_voltage(samples=SAMPLES, delay_ms=0):
    total = 0
    for _ in range(samples):
        total += adc.read_u16()
        if delay_ms:
            time.sleep_ms(delay_ms)
    avg = total / samples
    voltage = (avg / 65535.0) * VREF
    return voltage

# Send measurement over UART
def send_measurement(duty_percent: float):
    msg = "MEAS:{:.2f}\n".format(duty_percent)
    uart.write(msg.encode())

# Parse incoming UART commands
def handle_uart():
    global expected_setpoint
    if uart.any():
        line = uart.readline()
        if not line:
            return
        try:
            if isinstance(line, bytes):
                s = line.decode().strip()
            else:
                s = str(line).strip()
        except Exception:
            return
        # Expect "SET:xx"
        if s.startswith('SET:'):
            try:
                val = float(s.split(':',1)[1])
                expected_setpoint = val
                print("Received setpoint:", expected_setpoint)
            except Exception:
                pass
        else:
            print("UART RX (unknown):", s)

# Main loop: sample, compute duty, report
if __name__ == '__main__':
    print("ADC receiver starting: ADC GP{}".format(ADC_PIN))
    try:
        while True:
            # process any commands first
            handle_uart()

            # read averaged voltage from RC filter
            v = read_avg_voltage()
            # duty = Vavg / Vref * 100
            duty = (v / VREF) * 100.0
            # clamp
            if duty < 0.0:
                duty = 0.0
            if duty > 100.0:
                duty = 100.0

            # print and report
            print("Vavg={:.3f} V -> duty_est={:.2f}%".format(v, duty))
            send_measurement(duty)

            # short pause between measurements (depends on RC tau)
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("Stopped by user")