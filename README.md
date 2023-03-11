# WhatsGPT

> WhatsApp is a trademark of Meta, inc.

WhatsGPT is a Proof-of-Concept project to build a WhatsApp chat bot using official [WhatsApp API](https://business.whatsapp.com/developers/developer-hub). The bot would be powered by OpenAI GPT-3 to interpret messages sent to it, and fulfil it against realtime data that [Backend](./backend/README.md) module has access to.

## Features To-do List

Following serves as quick overview to project progress:

- [x] WhatsApp API Webhook:
  - [x] User should be able to send message to chat bot.
  - [x] User should receive an echo to message he sent.
- [ ] GPT-3 Integration:
  - [ ] Rather than getting echo of the message, User should receive an answer as provided by GPT-3.
- [ ] Realtime Data Integration:
  - [ ] Rather than getting responses compiled by GPT-3, User should receive an answer that reflect information bound to realtime data.
- [ ] Messages Log:
  - [ ] Admin should be able to view a log of all messages and responses from Dashboard.
  - [ ] Admin should be able to mark certain messages with different markers for later action.


## Technical Details

- This project will use a monorepo to structure all of its component.
- It will use Python with [AIOHttp](https://pypi.org/project/aiohttp/) to build [Backend]('./backend/README.md').
- It will use [MongoDB](https://www.mongodb.com) as Database.
- It will use [Qwik](https://qwik.builder.io/) to build Dashboard.
