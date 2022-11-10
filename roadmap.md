# Data prototype roadmap

A general note that in no world will the development be quite as linear as laid out here.
There will always be ideas that spark an afternoon of "What if I tried XYZ, how hard is that?"

This is primarily folloing a "breadth-first" approach


## Phase 1: Low-level artists, Data pipeline

The purpose of some of the earliest work is to lay foundations without direct regard for replicating existing APIs.
To be clear, all properties of these artists that are used by existing APIs must be present, but explicitly leaving out things like default behavior.

Including:
  - Patches (and most-all subclasses)
  - Line2D
  - Images (various)
  - Collections (various)
  - Text/annotations
  - Legend
  - Unit handling
  - Data pipeline

Explicitly not including in the first set:
  - Axis/Axes/Figure artists
  - Tick
  - Hyper-specific use case artists like QuiverKey/Table (these can be added when focusing on that usecase)

These artists carry some of the overall architectural decisions to be made about this API, and pinning them in too early is likely to paint us in corners that will be more difficult to reverse course on rather than holding off until some of the API basics are worked out

Questions to be answered during this phase:
  - Do the lowest level artists handle defaults for expected data keys? (lean NO, make it "cranky", build on top of these)
  - Do these artists use the same inheritance structure as existing artists?
  - What are the naming (or perhaps rather name-spacing?) conventions to use
  - Who wraps who? i.e. does the new code call into existing artists or implement the artists themselves and old code will then be modified to tap into new api?
  - What datatypes and other information are useful in data descriptors?
  - Consider the information flow of some things like transforms -- can data be queried without a transform? only sometimes? 

As a result of some of this, these artists may be somewhat painful to use, as they require being much more explicit than most existing interfaces.

### Parallel work that is not directly "low level artists"

- Documenting and working with existing Units code
- wrappers around some higher level artists to test the Data side of the project, developing better descriptions 
- Gather a library of example use cases to serve as end goals



## Phase 2: Higher-level artists

This phase solidifies some of the core ideas linking the Data layer and the Artist layer.

This will include focusing on many of the common Axes functions which return artists, including `plot`, `scatter`, `pcolor`, `contour`, etc.

Questions to be answered during this phase:
 - Unit handling (finalization)
 - Can the Data API be useful outside of mpl?
 - What is needed for full API compatibility such that existing methods can be rewritten to use the new API?
 - How should axes/axis/figures/ticks be handled?
 - How does the Data layer interact with third party libraries?
 - When (and what portions) does code get merged into matplotlib itself/added as dependencies?
 - Consider composition of artists into more complex artists (some ideas already reprepresented see Error Bar for example)
 - Are additional tests needed?

## Phase 3: Exploring new features enabled by this API

Items to consider:
 - Serialization of figures and interplay with other plotting libraries
 - Implementing Axes/Figures/Ticks changes that were decided in previous phase if they were "desireable, but not yet"
 - Are new Artist types desirable/made easier to manage by the Data layer?

## Phase 4: Extend support for domain specific libraries

Items to consider:
 - Documentation aimed specifically at authors of such libraries
 - Creating "rough draft" support for some key libraries (pandas, xarray, others that mpl maintainers are involved with)

