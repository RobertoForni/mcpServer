# Email Topic Classification

Classify every incoming email into exactly one category.

| Category           | Keywords and Signals                                         | Action        |
|--------------------|--------------------------------------------------------------|---------------|
| Task Interface     | picking list, task, order, high-level, WMS tasks             | Search docs   |
| Bin Interface      | bin control, low-level, bin movement, preparation            | Search docs   |
| Port Interface     | custom port, conveyor, port hardware, bin exchange           | Search docs   |
| Log Publisher      | events, event stream, bin location, status updates           | Search docs   |
| Authentication     | API key, token, login, credentials, 401, 403                | Search docs   |
| Error or Bug       | error, failed, timeout, not working, 500, exception         | Escalate      |
| General            | getting started, overview, which interface, comparison       | Search docs   |
| Out of Scope       | pricing, license, contract, roadmap, feature request         | Escalate      |
| Urgent or Angry    | ASAP, unacceptable, third time, escalate, manager            | Escalate      |

## Priority Rules

1. If the email matches Urgent or Angry, always escalate regardless of topic
2. If the email matches Error or Bug, escalate and include troubleshooting steps if available
3. If the email matches Out of Scope, escalate to sales or account team
4. For all other categories, search docs and draft a reply
