type:: notes
category:: meetings
created:: [[Feb 15th, 2025]]

- # Meeting Notes
  collapsed:: false

- ## Team Meeting - February 15, 2025
  - Discussed project timeline
    collapsed:: true
    - Sprint planning for next month
      id:: e95597dc-4b59-4640-98f7-53c949bd0616
    - Reviewed current sprint progress
      id:: 67a45c2e-529c-4831-b069-dd6f8e8d1234
    - Identified bottlenecks in the development process

  - Action items:
    - TODO Update roadmap document
      id:: 3c45d2f-639d-5942-c170-ee7f9e9e5432
      - TODO Find where the document is stored
      - TODO Adjust date
      - TODO Share link with the team
    - TODO Schedule one-on-one meetings with team members
    - DONE Share meeting minutes with stakeholders

- ## Architecture Review - February 10, 2025
  - Main points:
    - Need to refactor [[database]] schema
    - Discussed migration to [[microservices]]
      - {{embed ((3c45d2f-639d-5942-c170-ee7f9e9e5432))}}
    - Evaluated [[cloud providers]]

  - Decisions:
    - #+BEGIN_NOTE
      The team decided to proceed with the AWS migration in Q2.
      This decision was based on cost analysis and scalability requirements.
      #+END_NOTE

- ## Query Test
  - {{query (and (page "Meeting") (task TODO))}}

- ## References
  - See [[project timeline]] for deadlines 