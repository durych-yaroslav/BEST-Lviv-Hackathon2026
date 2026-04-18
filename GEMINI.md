# Instructions for AI Assistants (Gemini/Antigravity)

- **API Documentation (`README.md`)**: The root `README.md` file contains the complete REST API documentation. It includes:
  - Precise JSON request and response contracts.
  - Endpoint structures and HTTP methods.
  - Available query filters (such as `problem` and `location`).
  - Security and authorization definitions.

- **STRICT MANDATE**: You MUST strictly adhere to the API documentation defined in the `README.md`. It is the single source of truth. Do not hallucinate endpoints, fields, or behaviors not explicitly present in the documentation. Always refer to it when writing backend handlers or frontend integrations.


**Problem Context:**
In United Territorial Communities (UTCs), there is a systemic discrepancy between the actual physical state of assets (real estate, land, and resource usage) and the data recorded in official government registries. These inconsistencies arise from:
- A lack of automated data synchronization between disparate systems.
- Heavy reliance on manual, error-prone accounting processes.
- Limited capabilities to audit and control asset utilization effectively.

This ultimately leads to:
1. **Loss of Revenue:** Missed taxation or leasing opportunities due to unaccounted or misclassified properties.
2. **Inefficient Resource Management:** Poor strategic planning caused by inaccurate data.
3. **Lack of Transparency:** Fragmented records hinder municipal accountability and trust.