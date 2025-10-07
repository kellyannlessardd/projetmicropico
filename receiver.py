from machine import ADC, Pin, UART
import time

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