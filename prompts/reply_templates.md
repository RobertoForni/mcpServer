# Reply Templates

## 1: Task vs Bin Interface

Customer asks: Which interface should we use?

Reply:

Hi [Name],

The Task Interface is the simpler option. It operates at the picking list
level and AutoStore handles grouping, preparation, and optimization.

The Bin Interface gives your WMS more control but requires you to manage
bin movements, grouping, and optimization logic.

Key differences:

- Task Interface: Higher-level abstraction. Your WMS sends picking lists
  and AutoStore manages the bin operations. Simpler to implement.
- Bin Interface: Lower-level control. Your WMS manages individual bin
  movements, grouping, and optimization. More flexible but more complex.

Each installation must choose one. They cannot be combined.

See: https://interface.autostoresystem.com/docs/general-documentation-task-interface

Best regards,
AutoStore Interface Support


## 2: Port Interface

Customer asks: We have custom conveyor hardware at the ports.

Reply:

Hi [Name],

You need the Port Interface. It synchronizes bin insertion and removal
between the Grid and your custom Ports. It works with both the Task
Interface and the Bin Interface.

Standard AutoStore Port hardware does not need the Port Interface.
Bin exchange is handled automatically by AutoStore.

See: https://interface.autostoresystem.com/docs/general-documentation-port-interface

Best regards,
AutoStore Interface Support


## 3: Log Publisher

Customer asks: Do we need the Log Publisher with Task Interface?

Reply:

Hi [Name],

No, the Log Publisher is not required when using the Task Interface.

The Log Publisher sends an event stream with information about physical
Bin locations and preparation status. This information is:

- Required for Bin Interface implementations
- Optional for Task Interface implementations. You may use it for
  certain optimizations, but it is not necessary.

See: https://interface.autostoresystem.com/docs/general-documentation-log-publisher

Best regards,
AutoStore Interface Support


## 4: Escalation - System Issue

Customer reports: API returning 500 errors

Reply:

Hi [Name],

I am sorry to hear you are experiencing issues. I have flagged this for
our technical team as a priority.

To help us investigate, could you provide:

- The exact API endpoint(s) returning errors
- The timestamp when the errors started
- Your system or site identifier
- Any recent changes to your integration

Our team will follow up within [SLA] hours.

Best regards,
AutoStore Interface Support


## 5: Escalation - Out of Scope

Customer asks: About pricing, licensing, or contracts

Reply:

Hi [Name],

Thank you for your inquiry. I have forwarded this to our account team
who can assist with licensing and commercial questions.

They will be in touch within [SLA] business days.

Best regards,
AutoStore Interface Support
