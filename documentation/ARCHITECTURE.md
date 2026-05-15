# Architecture Overview

This project uses a **React frontend** with a **Python (Flask) backend** and follows a **Layered Architecture with MVC principles**.

The **View layer** is handled by React, which renders the user interface and captures user interactions. The **Controller layer** is implemented using Flask routes, which handle HTTP requests, validate input, and coordinate application logic. The **Model layer** consists of database models (e.g., using SQLite with SQLAlchemy) and represents the system’s data, such as users and mission logs.

Additionally, the backend communicates with an external **Virtual Robot API**, which is treated as a separate service. This architecture ensures clear separation of concerns, making the system easier to maintain and scale.

## Architecture Diagram

```mermaid
flowchart TB

    subgraph Frontend
        UI[React UI]
    end

    subgraph Backend
        Controller[Flask Controllers]
        Service[Business Logic]
        Model[Database Models]
    end

    DB[(Database)]
    Robot[Virtual Robot API]

    UI --> Controller
    Controller --> Service
    Service --> Model
    Model --> DB
    Service --> Robot