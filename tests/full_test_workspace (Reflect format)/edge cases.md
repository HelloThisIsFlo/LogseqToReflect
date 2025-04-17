# Edge Cases

tags:: project, urgent

## 1. Macro Blocks


## 2. Inline Properties

- Task with inline properties
  priority:: high
  background-color:: yellow
  id:: 1234-5678

## 3. Task Hierarchies

- [ ] Parent task
  - [ ] Subtask in progress
    - [x] Completed sub-subtask
  - [ ] Waiting on input
  - [x] ~~Cancelled task~~

## 4. List Types and Indentation

- Bullet list item
  1. Ordered subitem one
  1. Ordered subitem two
  - Back to bullet

## 5. Links

- Markdown link: [Reflect](https://reflect.app)
- LogSeq link: [[Nonexistent Page]]
- Link with special chars: [[Complex Page (v2)]]

## 6. Attachments/Media

- Embedding image: ![[Assets Diagram.png]]
- PDF attachment: [Quarterly Report.pdf](assets/Q1_Report.pdf)

## 7. Empty Content After Cleanup

- property:: value
- unused:: remove_me

## 8. Special Formatting

Inline math: $E = mc^2$

Code block:

```python
def sample():
    return "Hello, 😊"
```

## 9. Query Blocks


## 10. Naming and Special Characters

- [[Page-with-hyphens and Underscores]]