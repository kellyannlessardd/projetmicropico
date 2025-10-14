from machine import UART
import time

# Select role: 'tx' or 'rx'
MODE = 'tx'  # change to 'rx' on the receiving Pico

# UART configuration
UART_ID = 0
BAUD = 115200

uart = UART(UART_ID, BAUD)


def send_hello(interval_s=1.0):
    """Send the exact bytes 'Hello World\n' exactly once then return."""
    try:
        uart.write(b'Hello World\n')
    except Exception:
        # ignore UART errors on best-effort send
        pass


def receive_loop():
    """Read UART lines and print the message text when a line arrives."""
    try:
        while True:
            if uart.any():
                line = uart.readline()
                if not line:
                    continue
                # uart.readline() may return bytes or str depending on environment
                if isinstance(line, bytes):
                    try:
                        s = line.decode().strip()
                    except Exception:
                        s = str(line).strip()
                else:
                    s = str(line).strip()
                # Print only the exact message text
                print(s)
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    if MODE == 'tx':
        send_hello()
    else:
        receive_loop()
