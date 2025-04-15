# Wikilinks Test // Wiki Links Test // wikilinks/Test page

type:: documentation
category:: testing

# Wikilinks Test File

## Simple Links
- Basic wikilink: [[Simple Link]]
- With underscores: [[My_awesome_page]]
- Title case test: [[The Importance of Good Formatting]]

## Hierarchical Links
- Path with lowercase parts: [[aws/iam/Group in Space]] <- Should be [[aws/iam/Group in Space]]
- Multiple levels: [[project/documentation/User Guide]]
- Mixed case test: [[the/quick/Brown Fox]]

## Special Cases
- Link inside a task: TODO Check the [[database/Table Schema]] <- Should title case
- Link in an indented bullet:
- This has a [[nested/Link in Text]]
- Another with [[Complex_name_with_underscores]] <- Should keep as is

## Reference Examples
- See also [[database/backups/Daily Schedule]] for more information
- Related: [[The Quick Brown Fox]] jumped over [[The Lazy Dog]]