# OrionSmartlink

## Overview

**OrionSmartlink** is a Python-based system for automated collection, processing, and storage of egg count data from multiple aviary devices. It integrates with Orion hardware controllers over TCP/IP, processes the data, and stores results in a SQL Server database. The project provides both scheduled background jobs and a FastAPI-powered REST API for on-demand data processing.

---

## Architecture

- **Domain Layer**: Defines interfaces and entities (e.g., `EggCount`, repository interfaces).
- **Infrastructure Layer**: Implements device communication (`OrionClient`) and database access (`SqlServerRepository`).
- **Application Layer**: Contains use cases (e.g., `ProcessEggCountsUseCase`) that orchestrate domain logic.
- **Scheduler**: Uses APScheduler to periodically collect egg counts from all configured aviaries.
- **API Layer**: Exposes endpoints via FastAPI for on-demand data processing.
- **Configuration**: Uses `.env` and Pydantic models for flexible, environment-based configuration.

---

## Key Components and How They Work

### 1. Device Communication: `OrionClient` (`src/infrastructure/orion/client.py`)

This class is responsible for communicating with Orion devices over TCP/IP to fetch egg count data.

**Key Functions:**

- `__init__(self, ip, port, devcmd, num_rows, target_cmd, response_size)`:  
  Initializes the client with device-specific parameters such as IP address, port, command templates, and expected response size.

- `date_to_orion_hex(self, target_date_str: str) -> str`:  
  Converts a date string (e.g., "2025-06-09") into a hexadecimal timestamp format required by the Orion device protocol.  
  **Why:** Orion devices expect commands with a specific timestamp format; this function ensures the correct conversion.

- `build_init_cmd(self, date: str) -> str`:  
  Constructs the initialization command string to be sent to the device, including a checksum for integrity.  
  **Why:** The device requires a properly formatted command with a checksum to start communication.

- `fetch_egg_counts(self, aviary_id: int, date: str) -> Optional[List[int]]`:  
  Main function to connect to the device, send the initialization command, receive the response, and parse the egg counts.  
  **Why:** This is the core function that retrieves the actual data from the hardware, handling connection, command sending, and response parsing.

**Summary:**  
`OrionClient` abstracts all the low-level details of talking to the Orion hardware, so the rest of the system can simply call `fetch_egg_counts` and get a list of egg counts for a given aviary and date.

---

### 2. Database Access: `SqlServerRepository` (`src/infrastructure/database/sql_server_repository.py`)

This class handles all interactions with the SQL Server database, including looking up lot IDs and inserting/updating egg count records.

**Key Functions:**

- `get_lote_id(self, aviario_id: int, count_date: date) -> Optional[int]`:  
  Connects to the database and retrieves the `lote_id` (batch ID) for a given aviary and date.  
  **Why:** The stored procedure for inserting egg counts requires a valid lot ID; this function ensures it is available.

- `upsert_egg_counts(self, aviario_id: int, count_date: date, counts: List[int], fila_mapping: dict) -> bool`:  
  For each row (fila) in the aviary, calls a stored procedure (`sp_insertar_actualizar_regdia_huevos_orion`) to insert or update the egg count.  
  - Iterates over the counts and their corresponding fila mapping.
  - Executes the stored procedure for each fila.
  - Handles database transactions, commits on success, and rolls back on error.
  - Logs results and errors for each fila.
  **Why:** This function ensures that all egg count data is reliably written to the database, handling both new inserts and updates, and providing robust error handling.

**Summary:**  
`SqlServerRepository` abstracts all database logic, so the rest of the system can simply call `upsert_egg_counts` and not worry about SQL details or transaction management.

---

### 3. Use Case: `ProcessEggCountsUseCase` (`src/application/use_cases/process_egg_counts.py`)

Orchestrates the process of fetching egg counts from a device and storing them in the database.

**Key Functions:**

- `execute(self, aviary_id: int, count_date: date) -> Optional[EggCount]`:  
  - Calls `fetch_egg_counts` on the Orion client.
  - Calls `upsert_egg_counts` on the database repository.
  - Returns an `EggCount` entity if successful, or `None` if any step fails.
  **Why:** Encapsulates the business logic for a single egg count processing operation, making it reusable for both scheduled jobs and API requests.

---

### 4. Scheduler: `EggCountScheduler` (`src/scheduler/egg_count_scheduler.py`)

Runs as a background job, periodically triggering egg count collection for all aviaries.

**Key Functions:**

- Initializes the scheduler and sets up jobs to run at specific times.
- For each aviary, creates an `OrionClient` and a `SqlServerRepository`, then runs the use case.
- Handles retries and logs results.

**Why:** Automates the data collection process, ensuring regular and reliable updates without manual intervention.

---

### 5. API: FastAPI (`src/presentation/api/v1/routes.py`)

Exposes a REST API for on-demand processing.

**Key Functions:**

- `/egg_counts` POST endpoint:  
  Accepts an aviary ID and date, runs the use case, and returns the result.
- Uses Pydantic models for request and response validation.
- Automatically generates Swagger documentation at `/docs`.

**Why:** Allows external systems or users to trigger egg count processing as needed.

---

### 6. Configuration

- **`.env`**:  
  Stores device and block configuration, database credentials, and other environment-specific settings.
- **`settings.py`**:  
  Loads and parses configuration from `.env` using Pydantic models.

**Why:** Keeps sensitive and environment-specific data out of the codebase, making the system flexible and secure.

---

## How It Works

1. **Configuration Loading**:  
   On startup, the system loads aviary and database configuration from `.env` via `settings.py`.

2. **Scheduled Jobs**:  
   The scheduler runs at configured times, iterates through all aviaries, and:
   - Connects to each device.
   - Fetches egg counts.
   - Stores results in the database.
   - Retries failed aviaries up to two times.

3. **API Usage**:  
   You can POST to `/egg_counts` with an aviary ID and date to trigger processing for a specific aviary and date.

---

## Running the Project

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

- Edit `.env` to set database credentials and aviary block configurations.

### 3. Start the API Server

```bash
uvicorn src.main:app --host=localhost --port=8000 --reload
```
- Access Swagger UI at [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Start the Scheduler

If the scheduler is not started automatically, you can run it as a script or integrate it into your main FastAPI startup event.

---

## API Example

**POST** `/egg_counts`

```json
{
  "aviary_id": 15,
  "date": "2025-06-09"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Egg counts updated successfully",
  "data": {
    "aviary_id": 15,
    "date": "2025-06-09",
    "egg_counts": [123, 456, ...]
  }
}
```

---

## Logging

- Logs are written to `./src/logs/egg_counts.log` and to the console.
- Timestamps are in Argentina time.

---

## Troubleshooting

- **Database errors?**  
  Check `.env` credentials and network connectivity to SQL Server.
- **Device errors?**  
  Check device IPs, network, and command configuration in `.env`.

---

## License

This project is proprietary to Kevin Sanchez Galeano.

---