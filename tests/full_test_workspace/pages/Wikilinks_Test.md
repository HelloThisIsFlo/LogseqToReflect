alias:: Wiki Links Test, wikilinks/test page
type:: documentation
category:: testing

# Wikilinks Test File

- ## Simple Links
  - Basic wikilink: [[simple link]]
  - With underscores: [[my_awesome_page]]
  - Title case test: [[the importance of good formatting]]

- ## Hierarchical Links
  - Path with lowercase parts: [[aws/iam/group in space]] <- Should be [[aws/iam/Group in Space]]
  - Multiple levels: [[project/documentation/user guide]]
  - Mixed case test: [[The/Quick/brown fox]]

- ## Special Cases
  - Link inside a task: TODO Check the [[database/table schema]] <- Should title case
  - Link in an indented bullet:
    - This has a [[nested/link in text]]
    - Another with [[complex_name_with_underscores]] <- Should keep as is

- ## Reference Examples
  - See also [[database/backups/daily schedule]] for more information
  - Related: [[the quick brown fox]] jumped over [[the lazy dog]] 