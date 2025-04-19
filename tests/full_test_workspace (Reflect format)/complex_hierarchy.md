# Complex Hierarchy

## [[What I've Done Today]]
- [[Implement Tracing Support in Core Platform]]
	- Started mapping out the different request flow
		- Had some very nice **breakthroughs**! 😃
			- ==#### What works:==
				- Service A
					- Everything works ✅
				- Service B
					- **Caveat:** Client actually does 2 calls
						- The calls
							- `fetchMetadata`
							- `getResponse`
						- That's why we get 2 [[Dt Trace Id]]s ...
							- ... but the second [[Dt Trace Id]] has **all the info we need** 🎉
				- `resolveData`
					- This is what's actually called by the internal `fetch_dataset` method
			- ==#### What doesn't work:==
				- The fallback path via `get_fallback_stream?`
	- I found a lot of `<root span not yet received>` → Will need to follow up with [[Engineer X]]
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
- ### [[Weekly Check-in with Team Lead]]
	- [x] ~~Set a meeting for discussing the progress on [[Implement Tracing Support in Core Platform]] with the team~~
		- [[Team Lead]] was quite happy with the initiative
		- I think it would help in two ways
			1. Reduce the knowledge silos
				- By exposing the team to the tracing implementation
			1. Gain insight from the team
				- They may already have solutions to current blockers
- ### Reflection on Team Dynamics
	- Had a discussion focused on alignment and team collaboration
		- Some concerns about perceived delivery speed came up
	- The key challenge is navigating workstreams with high uncertainty
		- Suggested approach: time-boxed technical spike
			1. Investigate for X days
			1. Present learnings
			1. Reassess scope and next steps
		- If full delivery is mandatory:
			- Break down scope and deliver smallest increment
			- Escalate if additional support or resources are needed
	- Identified an area for potential improvement:
		- **Risk that lack of visible output may affect perception of progress**
			- ==Recommendation: proactively clarify expectations with stakeholders==
				- ==Example question: “Is the current delivery pace aligned with expectations, or should we course-correct?”==
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