# Edge Cases

- ## 1. Macro Blocks
  - > ## ℹ️ This is a note block containing [[Link]] and - [ ] Task
  - > ## ⚠️ This is a warning block with ![[Image.png]] embedded.
  - > ## ‼️ Important information goes here.
- ## 2. Inline Properties
  - ==Task with inline properties==
- ## 3. Background Color
  - ==[[Super Important Topic]] that should be highlighted==
  - #### ==Highlighted Title in bullet list==
- ## 4. Task Hierarchies
  - [ ] Parent task
    - [ ] Subtask in progress
      - [x] Completed sub-subtask
    - [ ] Waiting on input
  - [x] ~~Cancelled task~~
- ## 5. List Types and Indentation
  - Bullet list item
    1. Ordered subitem one
  1. Ordered subitem two
  - Back to bullet
- ## 6. Links
  - Markdown link: [Reflect](https://reflect.app)
  - LogSeq link: [[Nonexistent Page]]
  - Link with special chars: [[Complex Page (v2)]]
- ## 7. Attachments/Media
  - Embedding image: ![[Assets Diagram.png]]
  - PDF attachment: [Quarterly Report.pdf](assets/Q1_Report.pdf)
- ## 8. Empty Content After Cleanup
  - Some content
  - Some more content
- ## 9. Special Formatting
  - Inline math: $E = mc^2$
  - Code block:
    - ```python
      def sample():
      return "Hello, 😊"
      ```

- ## 10. Query Blocks
  - #+BEGIN_QUERY
    {:query [:find ?title :where [?p :block/name ?title]]}
    #+END_QUERY

- ## 11. Naming and Special Characters
  - [[Page-with-hyphens and Underscores]]

- ## 12. Tasks in headings
  - [ ] ## Some task
    - [x] # Another task
      - [ ] ### One more task
- ## 13. Embedding a block in a page with type
  - This is a test _hello test ([[With Some Backlink in Title and Topic Another One]])_ bla bla

- ## 14. Code blocks with hashtags
  - ```python
    # This is a code block with a hashtag
    print("Hello, world!")
    ```
  - Now under a deep nested hierarchy
    - Level 2
      - Level 3
        - Level 4
          - Level 5
            - Level 6
              - Level 7
                - Level 8
                  - ```
                    print("Hello, world!")
                    # Some comment
                    #                  some other comment
                    ```

- ## 15. Nested embeds
  - Level 1
    - Level 2
      - Level 3
        - Level 4
          - Level 5
            - #### Level 6A
              - _[ ] Implement authentication system ([[Project Alpha]])_
              - _[ ] Implement authentication system ([[Project Alpha]])_
            - #### Level 6B
              - First conversation
                _[ ] Implement authentication system ([[Project Alpha]])_
              - The next day
                _[ ] Implement authentication system ([[Project Alpha]])_

- ## 16. Inline tags
  - this is a test [[insight]]
  - I'm wondering XYZ [[follow-up]]
  - I'm wondering XYZ [[with-capital_letter]]

  - [AMI Catalog on the aws/console](https://eu-west-1.console.aws.amazon.com/ec2/home?AMICatalog&region=eu-west-1#AMICatalog:)
  - Level 1
    - ```
      some code
      hello #345
      ```
- ## 17. Add new blocks for code blocks
  - Some code
    - ```python
      print("Hello, world!")
      ```
  - Level 2
    - Some other code
      - ```python
        print("Hello, world!")
        ```
- ## 18. Embed from files with url-encoded filename
  - _Hello hello ([[This Is a Test%3a with Some %22quoted Text%22 It Should Be Converted]])_