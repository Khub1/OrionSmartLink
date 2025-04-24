from pydantic import BaseModel
from typing import Dict
import os
from dotenv import load_dotenv
import json

# Load .env file
load_dotenv()

# Database Settings
DATABASE_SETTINGS = {
    "server": os.getenv("DATABASE_SERVER", "172.16.1.202"),
    "name": os.getenv("DATABASE_NAME", "grupomaehara"),
    "user": os.getenv("DATABASE_USER", "your_username"),
    "password": os.getenv("DATABASE_PASSWORD", "your_password"),
    "driver": os.getenv("DATABASE_DRIVER", "ODBC Driver 17 for SQL Server"),
}

class AviaryConfig(BaseModel):
    ip: str
    port: int
    devcmd: str
    name: str
    num_rows: int
    fila_mapping: Dict[int, int]
    target_cmd: str
    response_size: int

def load_aviary_configs() -> Dict[int, AviaryConfig]:
    configs = {}
    
    # Shared aviary settings
    default_port = int(os.getenv("AVIARY_PORT", 5843))
    default_num_rows = int(os.getenv("AVIARY_NUM_ROWS_DEFAULT", 48))
    default_response_size = int(os.getenv("AVIARY_RESPONSE_SIZE_DEFAULT", 210))
    default_fila_mapping = json.loads(os.getenv("AVIARY_FILA_MAPPING_DEFAULT", "{}"))
    
    # Load blocks
    blocks = [
        ("BLOCK_A1_A8", os.getenv("BLOCK_A1_A8"), os.getenv("BLOCK_A1_A8_IP")),
        ("BLOCK_A9_A12", os.getenv("BLOCK_A9_A12"), os.getenv("BLOCK_A9_A12_IP")),
        ("BLOCK_B2_B8", os.getenv("BLOCK_B2_B8"), os.getenv("BLOCK_B2_B8_IP")),
        ("BLOCK_B9_B11", os.getenv("BLOCK_B9_B11"), os.getenv("BLOCK_B9_B11_IP")),
        ("BLOCK_H1", os.getenv("BLOCK_H1"), os.getenv("BLOCK_H1_IP")),
        ("BLOCK_H3", os.getenv("BLOCK_H3"), os.getenv("BLOCK_H3_IP")),
    ]
    
    for block_name, block_json, block_ip in blocks:
        if not block_json or not block_ip:
            print(f"Warning: Missing config for {block_name}")
            continue
        try:
            block_configs = json.loads(block_json)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON for {block_name}: {e}")
            continue
        for config in block_configs:
            aviary_id = config["id"]
            configs[aviary_id] = AviaryConfig(
                ip=block_ip,
                port=default_port,
                devcmd=config["devcmd"],
                name=config["name"],
                num_rows=config.get("num_rows", default_num_rows),
                fila_mapping=config.get("fila_mapping", default_fila_mapping),
                target_cmd=config["target_cmd"],
                response_size=config.get("response_size", default_response_size),
            )
    
    return configs

AVIARY_CONFIGS = load_aviary_configs()
