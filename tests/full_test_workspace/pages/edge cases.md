

tags:: project, urgent

## 1. Macro Blocks

- #+BEGIN_NOTE
  This is a note block containing [[Link]] and - TODO Task
  #+END_NOTE
- #+BEGIN_WARNING
  This is a warning block with ![[image.png]] embedded.
  #+END_WARNING
- #+BEGIN_IMPORTANT
  Important information goes here.
  #+END_IMPORTANT

## 2. Inline Properties

- Task with inline properties
  some-property:: high
  background-color:: yellow

## 3. Background Color

- [[Super Important Topic]] that should be highlighted
  background-color:: yellow


## 4. Task Hierarchies

- TODO Parent task
  - DOING Subtask in progress
    - DONE Completed sub-subtask
  - WAITING Waiting on input
  - CANCELED Cancelled task

## 5. List Types and Indentation

- Bullet list item
  collapsed:: true
  - Ordered subitem one
    logseq.order-list-type:: number
  - Ordered subitem two
    logseq.order-list-type:: number
  - Back to bullet

## 6. Links

- Markdown link: [Reflect](https://reflect.app)
- LogSeq link: [[Nonexistent Page]]
- Link with special chars: [[Complex Page (v2)]]

## 7. Attachments/Media

- Embedding image: ![[assets/diagram.png]]
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

- [[Page-With-Hyphens_and_Underscores]]

## 12. Tasks in headings

- ## TODO Some task
	- # DONE Another task
		- ### WAITING One more task