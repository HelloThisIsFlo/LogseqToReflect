## [[What I've done today]]
	- [[jira/Implement Tracing Support in Core Platform]]
		- Started mapping out the different request flow
			- Had some very nice **breakthroughs**! 😃
				- #### What works:
				  background-color:: green
					- Service A
						- Everything works ✅
					- Service B
						- **Caveat:** Client actually does 2 calls
							- The calls
								- `fetchMetadata`
								- `getResponse`
							- That's why we get 2 [[dt/trace id]]s ...
								- ... but the second [[dt/trace id]] has **all the info we need** 🎉
					- `resolveData`
						- This is what's actually called by the internal `fetch_dataset` method
				- #### What doesn't work:
				  background-color:: red
					- The fallback path via `get_fallback_stream?`
		- I found a lot of `<root span not yet received>` => Will need to follow up with [[Engineer X]]
	- [[Editorial Planning]]
		- Met with [[Lead Reviewer]] and we agreed on a timeline
		- I've already asked [[Contributor A]] for a summary of their work, I'll highlight:
			- Reporting dashboard
			- Notification routing
			- New feature launch (will cover this in a separate post next week)
			- Maybe:
				- Mention fix for `ORDER BY` issue
					- (undecided — depends on scope of bugfixes we include)
					- Not user-facing, since the affected version isn’t deployed yet
- ### [[Weekly Check-In with Team Lead]]
	- CANCELLED Set a meeting for discussing the progress on [[jira/Implement Tracing Support in Core Platform]] with the team
		- [[Team Lead]] was quite happy with the initiative
		- I think it would help in two ways
			- Reduce the knowledge silos
			  logseq.order-list-type:: number
				- By exposing the team to the tracing implementation
			- Gain insight from the team
			  logseq.order-list-type:: number
				- They may already have solutions to current blockers
- ### Reflection on Team Dynamics
	- Had a discussion focused on alignment and team collaboration
		- Some concerns about perceived delivery speed came up
	- The key challenge is navigating workstreams with high uncertainty
		- Suggested approach: time-boxed technical spike
			- Investigate for X days
			  logseq.order-list-type:: number
			- Present learnings
			  logseq.order-list-type:: number
			- Reassess scope and next steps
			  logseq.order-list-type:: number
		- If full delivery is mandatory:
			- Break down scope and deliver smallest increment
			- Escalate if additional support or resources are needed
	- Identified an area for potential improvement:
		- **Risk that lack of visible output may affect perception of progress**
			- Recommendation: proactively clarify expectations with stakeholders
			  background-color:: green
				- Example question: “Is the current delivery pace aligned with expectations, or should we course-correct?”
				  background-color:: yellow
					- *If aligned:* great, keep going with confidence
					- *If not:* adjust scope, cadence, or communication
- ### [[Flexible Work Policy]]
	- There's an internal policy that allows short-term remote work
	- Typical allowance:
		- 1 week flexible
		- 2 weeks during designated periods
	- #### Process
		- Request must be submitted 30 days ahead
		- Requires approval and standard HR documentation