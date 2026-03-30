# Test Cases

Run each test in Cursor AI chat using this prompt format:

    Read prompts/system_prompt.md and prompts/classification.md.
    Then draft a reply to this customer email:
    [paste test email here]


## Test 1: Factual - Interface Compatibility

Email: Can we use both Task Interface and Bin Interface together?
Must say: No, they cannot be combined. Each installation chooses one.
Must NOT: Suggest any workaround to combine them.


## Test 2: Classification - Port Interface

Email: We need to synchronize bin movements with our custom robotic arm at the port.
Must: Identify as Port Interface topic. Recommend Port Interface API.
Must NOT: Suggest Task or Bin Interface alone is sufficient.


## Test 3: Escalation - Angry Customer

Email: This is the third time I am writing. Your API has been down for 2 days and nobody is responding. I need to speak to a manager.
Must: Escalate. Empathetic tone. Ask for diagnostic details.
Must NOT: Attempt a technical fix or ignore the frustration.


## Test 4: Escalation - Out of Scope

Email: How much does the AutoStore Interface license cost?
Must: Escalate to sales or account team.
Must NOT: Guess at pricing or say it depends.


## Test 5: Ambiguous Question

Email: How do we get bin locations?
Must: Ask which interface they use. Explain that it is required for Bin Interface, optional for Task Interface via Log Publisher.
Must NOT: Assume which interface they have.


## Test 6: Not in Docs

Email: What is the maximum number of concurrent API connections supported?
Must: Acknowledge the docs do not specify this. Offer to escalate.
Must NOT: Fabricate a number.


## Test 7: Non-English

Email: Wir verwenden das Task Interface. Muessen wir auch den Log Publisher implementieren?
Must: Reply in English. Same answer as Template 3. Log Publisher is optional for Task Interface.
Must NOT: Reply in German or use complex English.


## Scoring

| Criteria                | Pass                       | Fail                        |
|-------------------------|----------------------------|-----------------------------|
| Factually accurate      | Uses only doc content      | Invents information         |
| Correct classification  | Right topic identified     | Wrong topic                 |
| Escalation when needed  | Flags for human review     | Attempts answer             |
| Links to documentation  | Includes doc URL           | No reference                |
| Tone                    | Professional, clear        | Casual, jargon-heavy        |
| Conciseness             | Direct answer, no filler   | Rambling or repetitive      |
