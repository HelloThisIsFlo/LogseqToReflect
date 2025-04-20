# Edge Cases

## 1. Macro Blocks

- > ## ℹ️ This is a note block containing [[Link]] and - [ ] Task
- > ## ⚠️ This is a warning block with ![[Image.png]] embedded.
- > ## ‼️ Important information goes here.

## 2. Inline Properties

- ==Task with inline properties==

## 3. Background Color

- ==[[Super Important Topic]] that should be highlighted==

- #### ==Highlighted Title in bullet list==

## 4. Task Hierarchies

- [ ] Parent task
  - [ ] Subtask in progress
    - [x] Completed sub-subtask
  - [ ] Waiting on input
  - [x] ~~Cancelled task~~

## 5. List Types and Indentation

- Bullet list item
  1. Ordered subitem one
  1. Ordered subitem two
  - Back to bullet

## 6. Links

- Markdown link: [Reflect](https://reflect.app)
- LogSeq link: [[Nonexistent Page]]
- Link with special chars: [[Complex Page (v2)]]

## 7. Attachments/Media

- Embedding image: ![[Assets Diagram.png]]
- PDF attachment: [Quarterly Report.pdf](assets/Q1_Report.pdf)

## 8. Empty Content After Cleanup

- property:: value
- unused:: remove_me

## 9. Special Formatting

Inline math: $E = mc^2$

Code block:

```python
def sample():
    return "Hello, 😊"
```

## 10. Query Blocks

- #+BEGIN_QUERY
  {:query [:find ?title :where [?p :block/name ?title]]}
  #+END_QUERY

## 11. Naming and Special Characters

- [[Page-with-hyphens and Underscores]]

## 12. Tasks in headings

- ## [ ] Some task
	- # [x] Another task
		- ### [ ] One more task

## 13. Embedding a block in a page with type

- This is a test _hello test ([[With Some Backlink in Title and Topic Another One]])_ bla bla

## 14. Code blocks with hashtags

```python
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

## 15. Nested embeds
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