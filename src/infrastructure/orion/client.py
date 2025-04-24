import socket
from datetime import datetime
from typing import List, Optional
from src.domain.interfaces.orion_repository import OrionDeviceRepository

class OrionClient(OrionDeviceRepository):
    def __init__(self, ip: str, port: int, devcmd: str, num_rows: int, target_cmd: str, response_size: int):
        self.ip = ip
        self.port = port
        self.devcmd = devcmd
        self.num_rows = num_rows
        self.target_cmd = target_cmd
        self.response_size = response_size

    def date_to_orion_hex(self, target_date_str: str) -> str:
        base_date = datetime(2025, 4, 7)
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
        delta_days = (target_date - base_date).days
        return f"{0x0467F3157F + delta_days * 0x15180:X}"

    def build_init_cmd(self, date: str) -> str:
        hex_timestamp = self.date_to_orion_hex(date)
        cmd = f"{self.devcmd}{hex_timestamp}"
        checksum = 0
        for char in cmd:
            checksum ^= ord(char)
        return f"{cmd}{checksum:02X}*\r"

    def fetch_egg_counts(self, aviary_id: int, date: str) -> Optional[List[int]]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)  # Connection timeout
            try:
                # Connect and send init command
                s.connect((self.ip, self.port))
                init_cmd = self.build_init_cmd(date)
                s.sendall(init_cmd.encode('ascii'))
                #####print(f">>> {init_cmd.strip()}")

                # Receive 67-byte init response
                init_response = s.recv(67)
                #####print(f"<<< {init_response.decode('ascii', errors='replace').strip()}")

                # Send count request
                s.sendall(self.target_cmd.encode('ascii'))
                #####print(f">>> {self.target_cmd.strip()}")

                # Get egg counts with short timeout
                s.settimeout(0.5)
                count_response = s.recv(self.response_size)
                ascii_response = count_response.decode('ascii', errors='replace').strip()
                #####print(f"<<< {ascii_response}")

                # Parse counts
                payload = ascii_response[15:-3]  # Remove header and *XX
                if len(payload) != self.num_rows * 4:
                    print(f"Invalid payload length: expected {self.num_rows * 4}, got {len(payload)}")
                    return None
                return [int(payload[i:i+4], 16) for i in range(0, len(payload), 4)]

            except socket.timeout:
                print("Timeout waiting for response")
                return None
            except socket.error as e:
                print(f"Socket error: {e}")
                return None
            finally:
                s.close()
