# AI Context and Instructions (gemini.md)

This file helps the AI assistant understand the project structure, how to read the API documentation, and how to use the Makefile.

## 1. API Documentation
When working with the API (creating new endpoints, testing, or updating logic), always read the documentation first.

* **API Specification:** `[PATH_TO_SWAGGER_FILE]` (e.g., `docs/swagger.yaml` or `api/openapi.json`)
* **Text Documentation:** `[PATH_TO_MARKDOWN_DOCS]` (e.g., `docs/api_reference.md`)

## 2. Makefile Usage
The project uses a `Makefile` to automate tasks. The AI should use these commands to build, test, and run the project.

* **Makefile Path:** `./Makefile`і

### Available Commands:
* `make run` - [DESCRIPTION: Start the local server]
* `make build` - [DESCRIPTION: Compile the project binary]
* `make test` - [DESCRIPTION: Run unit and integration tests]
* `make lint` - [DESCRIPTION: Run code linters]
* `make db-up` - [DESCRIPTION: Start database containers / run migrations]

## 3. Project Environment & Stack
* **Main Language:** [e.g., Golang]
* **Database:** [e.g., PostgreSQL]
* **System Environment:** [e.g., Linux / NixOS]

## 4. Rules for AI
1.  **Read the Docs:** Do not guess API structures. Always look at the paths provided in the API Documentation section.
2.  **Test the Code:** Suggest running `make test` or `make build` after making changes to the code.
3.  **Write Clean Code:** Keep the code efficient, well-structured, and suitable for a high-load environment. Do not overcomplicate solutions.