To run the Smart Hydration & Nutrition Advisor:

1.  **Ensure you have Python installed.**
2.  **Install the required dependencies** (if you haven't already):
    ```bash
    pip install fastapi uvicorn pydantic
    ```
3.  **Start the FastAPI backend:**
    ```bash
    uvicorn main:app --reload
    ```
    This will start the server, typically at `http://127.0.0.1:8000`. The `--reload` flag will automatically restart the server when you make changes to `main.py`.

4.  **Open your web browser** and navigate to `http://127.0.0.1:8000` to access the frontend.

You can then interact with the form to get hydration and nutrition recommendations.