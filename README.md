# Sentinel Enterprise API

**Sentinel Enterprise API** is a backend service built with [FastAPI](https://fastapi.tiangolo.com/) and [SQLModel](https://sqlmodel.tiangolo.com/) for managing access control. It powers mobile and dashboard applications used by **guards**, and **administrators**.

## Project Structure

```plaintext
sentinel-enterprise-api
├── src
│   ├── main.py          # Entry point of the FastAPI application
│   ├── database.py      # Database connection handling
│   ├── auth             # Directory for authentication and authorization
│   │   └── __init__.py  # Authentication utilities and JWT handling
│   ├── models           # Directory for SQLModel models
│   │   └── __init__.py  # Model definitions
│   ├── routers          # Directory for API routers
│   │   └── __init__.py  # API route definitions
│   ├── schemas          # Directory for Pydantic schemas
│   │   └── __init__.py  # Schema definitions
│   └── services         # Business logic layer
│       └── __init__.py  # Service definitions
├── requirements.txt     # Project dependencies
├── .env                 # Environment variables
└── README.md            # Project documentation
```

## Database Models

For detailed model relationships, see the `/src/models/` directory.

## Setup Instructions

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd sentinel-enterprise-api
   ```

2. **Create a virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the database:**
   - Create a `.env` file in the root directory and add your database connection string:

     ```plaintext
     DATABASE_URL=mysql+asyncmy://<username>:<password>@<host>:<port>/<database>
     ```

5. **Run the application:**

   ```bash
   uvicorn src.main:app --reload --host 127.0.0.1 --port 8000 --log-level debug
   ```

## Usage

- Access the API documentation at `http://127.0.0.1:8000/docs`.
- Use the endpoints defined in the routers to interact with the application.

## MCP Server

Sentinel Enterprise API includes a **MCP (Model Context Protocol)** to connect with MCP client applications. To test the MCP server, you can use the following configuration in your MCP client, like vscode, cursor or any other MCP client using their respective MCP configuration file:

```json
{
  "servers": {
    "sentinel-enterprise-mcp": {
      "url": "http://127.0.0.1:8000/mcp",
      "headers": {
        "Authorization": "Bearer <your-jwt-token>"
      }
    }
  }
}
```
