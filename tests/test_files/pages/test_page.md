alias:: Test Alias, Another/Alias

id:: abcd1234-5678-90ab-cdef-1234567890ab

- This is a test page
- TODO Test task 1
- DONE Test task 2
- DOING Test task 3

collapsed:: true

Some regular content with a block reference ((abcd1234-5678-90ab-cdef-1234567890ab))

:LOGBOOK:
CLOCK: [2023-01-15 Sun 10:00:00]--[2023-01-15 Sun 11:00:00] =>  01:00:00
:END:

#+BEGIN_SRC python
def hello():
    print("Hello, world!")
#+END_SRC

{{query (todo todo)}} 