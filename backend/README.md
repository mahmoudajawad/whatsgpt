# WhatsGPT Backend

Backend would serve the following purposes:
- [Stage 1] Serve a webhook that receives messages from Whatsapp API.
- [Stage 1] Log every message and response to Database.
- [Stage 1] Respond to messages with an echo.
- [Stage 2] Pipe every message to OpenAI GPT-3.
- [Stage 2] Respond to messages with response from GPT-3.
- [Stage 3] Convert message to machine language syntax.
- [Stage 3] Pipe syntax to processor against realtime data.
- [Stage 3] Respond to message with results of syntax processing.

These are broad points at this stage and may change as needed, however, they are laid as roadmap for Backend.

## Running Backend

Running Backend make use of following env variables set:
- `PORT`: (Optional) Port number to bind Backend to. Required if running using `docker-compose`.
- `OUTPUT`: (Optioal) One of `WHATSAPP`, `CONSOLE` to set where to report response of OpenAI model.
- `WHATSAPP_APP_ID`: WhatsApp API app ID.
- `WHATSAPP_API_TOKEN`: WhatsApp API app token.
- `OPENAI_API_KEY`: OpenAI API key.

You can either set them directly in your shell, or in `backend/.env` file.

If you are running Backend using `docker-compose` make sure to use `backend/.env` file.

## Developing Backend

Check [Contributing Guidelines](./CONTRIBUTING.md).

